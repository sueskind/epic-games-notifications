import datetime as dt
import subprocess
from time import sleep

import requests as req
import schedule

from . import epic


def _telegram_escaped_string(s):
    """Replaces characters in a string for Markdown V2."""
    for c in "_*[]()~>#+-=|{}.!":
        s = s.replace(c, "\\" + c)
    return s


class Notifier:
    TELEGRAM = "telegram"
    SIGNAL = "signal"

    def __init__(self, service, telegram_bot_token=None, signal_sender_number=None, country="US"):
        if service.lower() == Notifier.TELEGRAM:
            self.service = Notifier.TELEGRAM
            self.bot_token = telegram_bot_token
        elif service.lower() == Notifier.SIGNAL:
            self.service = Notifier.SIGNAL
            self.signal_sender_number = signal_sender_number
        else:
            raise ValueError("Supported services are 'signal' and 'telegram'.")

        self.country = country
        self.offers = None

    def update_offers(self):
        self.offers = epic.get_offers(self.country)

    def _send_telegram(self, current, upcoming, recipients):

        message = f"*Current*:\n{_telegram_escaped_string(current)}\n\n*Upcoming*:\n{_telegram_escaped_string(upcoming)}"

        for recp in recipients:
            params = {
                "chat_id": int(recp),
                "text": message,
                "parse_mode": "MarkdownV2"
            }

            # API Doc: https://core.telegram.org/bots/api#sendmessage
            telegram_send_fmt = "https://api.telegram.org/bot{}/sendMessage"
            res = req.get(telegram_send_fmt.format(self.bot_token), params=params)
            res.raise_for_status()

    def _send_signal(self, current, upcoming, recipients):
        message = f"Current:\n{_telegram_escaped_string(current)}\n\nUpcoming:\n{_telegram_escaped_string(upcoming)}"

        for recp in recipients:
            # signal-cli Doc: https://github.com/AsamK/signal-cli
            msg_out = subprocess.Popen(["echo", "-e", f"{message}"], stdout=subprocess.PIPE)
            signal = subprocess.Popen(["signal-cli", "-u", self.signal_sender_number, "send", recp],
                                      stdin=msg_out.stdout)
            signal.wait()

    def notify(self, recipients, show_days=False):
        """
        Gets the current offers and sends a Telegram notification.

        :param recipients: List of Telegram chat ids or Signal phone numbers of the receivers.
        :param show_days: Boolean, False if the offers' dates should be given, True for day difference. Default: False
        """

        if not self.offers:
            raise AttributeError("No offers registered. Did you run 'update_offers'?")

        current, upcoming = [], []
        for o in self.offers:
            if o.start_date < dt.datetime.now():
                current.append(o)
            else:
                upcoming.append(o)

        current = "\n".join(o.format_offer(True, show_days) for o in current)
        upcoming = "\n".join(o.format_offer(False, show_days) for o in upcoming)

        if self.service == Notifier.TELEGRAM:
            self._send_telegram(current, upcoming, recipients)
        else:
            self._send_signal(current, upcoming, recipients)

    def notify_weekly(self, recipients, dow, time, show_days=False, ignore_errors=False):
        """
        Run loop to send notification weekly on a given day of week.

        :param recipients: List of Telegram chat ids or Signal phone numbers of the receivers.
        :param dow: Integer, 0 = Monday, 1 = Tuesday, ..., 6 = Sunday
        :param time: String, clock time for the notification. Format: HH:MM
        :param ignore_errors: Boolean, set True to keep the loop running if any Exception is thrown. Default: False
        :param show_days: Boolean, False if the offers' dates should be given, True for day difference. Default: False
        """

        def job():
            self.update_offers()
            self.notify(recipients, show_days)

        if dow == 0:
            day_name = "Monday"
            schedule.every().monday.at(time).do(job)
        elif dow == 1:
            day_name = "Tuesday"
            schedule.every().tuesday.at(time).do(job)
        elif dow == 2:
            day_name = "Wednesday"
            schedule.every().wednesday.at(time).do(job)
        elif dow == 3:
            day_name = "Thursday"
            schedule.every().thursday.at(time).do(job)
        elif dow == 4:
            day_name = "Friday"
            schedule.every().friday.at(time).do(job)
        elif dow == 5:
            day_name = "Saturday"
            schedule.every().saturday.at(time).do(job)
        elif dow == 6:
            day_name = "Sunday"
            schedule.every().sunday.at(time).do(job)
        else:
            raise ValueError("Day of the week (dow) must be 0-6.")

        print(f"Notifying {recipients} every {day_name} at {time}.")

        if ignore_errors:
            print("Ignoring errors.")
            while True:
                try:
                    schedule.run_pending()
                except Exception as e:
                    print(f"Ignoring error: {e}")
                sleep(1)

        else:
            while True:
                schedule.run_pending()
                sleep(1)

    def notify_on_change(self, recipients, update_interval=300, initial=False, show_days=False, ignore_errors=False):
        """
        Run loop to send notification when the offers changed.

        :param recipients: List of Telegram chat ids or Signal phone numbers of the receivers.
        :param update_interval: Float, the seconds between refreshes. Default: 300
        :param initial: Boolean, whether to send a notification when starting the loop. Default: False
        :param ignore_errors: Boolean, set True to keep the loop running if any Exception is thrown. Default: False
        :param show_days: Boolean, False if the offers' dates should be given, True for day difference. Default: False
        """

        def offers_equal(offers1, offers2):
            set1, set2 = set(offers1), set(offers2)
            return len(set1 - set2) == len(set2 - set1) == 0

        print(f"Notifying {recipients} when offers change (refreshing every {update_interval} seconds).")

        self.update_offers()
        if initial:
            self.notify(recipients, show_days)

        last_offers = self.offers

        if ignore_errors:
            print("Ignoring errors.")
            while True:
                try:
                    sleep(update_interval)
                    self.update_offers()
                    if not offers_equal(last_offers, self.offers):
                        self.notify(recipients, show_days)
                        last_offers = self.offers
                except Exception as e:
                    print(f"Ignoring error: {e}")

        else:
            while True:
                sleep(update_interval)
                self.update_offers()
                if not offers_equal(last_offers, self.offers):
                    self.notify(recipients, show_days)
                    last_offers = self.offers
