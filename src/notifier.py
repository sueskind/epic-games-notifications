import datetime as dt
from time import sleep

import requests as req
import schedule

from . import epic

# API Doc: https://core.telegram.org/bots/api#sendmessage
TELEGRAM_SEND_URL_FMT = "https://api.telegram.org/bot{}/sendMessage"


def _escaped_string(s):
    """Replaces characters in a string for Markdown V2."""
    for c in "_*[]()~>#+-=|{}.!":
        s = s.replace(c, "\\" + c)
    return s


class Notifier:
    TELEGRAM = "telegram"
    SIGNAL = "signal"

    def __init__(self, service, bot_token=None, country="US"):
        if service.lower() == Notifier.TELEGRAM:
            pass
        elif service.lower() == Notifier.SIGNAL:
            pass
        else:
            raise ValueError("Supported services are 'signal' and 'telegram'.")

        self.bot_token = bot_token
        self.country = country
        self.offers = None

    def update_offers(self):
        self.offers = epic.get_offers(self.country)

    def notify(self, chat_ids, show_days=False):
        """
        Gets the current offers and sends a Telegram notification.

        :param chat_ids: List of Integers, Telegram chat ids of the receivers.
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

        message = f"*Current*:\n{_escaped_string(current)}\n\n*Upcoming*:\n{_escaped_string(upcoming)}"

        for cid in chat_ids:
            params = {
                "chat_id": cid,
                "text": message,
                "parse_mode": "MarkdownV2"
            }

            res = req.get(TELEGRAM_SEND_URL_FMT.format(self.bot_token), params=params)
            res.raise_for_status()

    def notify_weekly(self, chat_ids, dow, time, show_days=False, ignore_errors=False):
        """
        Run loop to send notification weekly on a given day of week.

        :param chat_ids: List of Integers, Telegram chat ids of the receivers.
        :param dow: Integer, 0 = Monday, 1 = Tuesday, ..., 6 = Sunday
        :param time: String, clock time for the notification. Format: HH:MM
        :param ignore_errors: Boolean, set True to keep the loop running if any Exception is thrown. Default: False
        :param show_days: Boolean, False if the offers' dates should be given, True for day difference. Default: False
        """

        def job():
            self.update_offers()
            self.notify(chat_ids, show_days)

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

        print(f"Notifying {chat_ids} every {day_name} at {time}.")

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

    def notify_on_change(self, chat_ids, update_interval=300, initial=False, show_days=False, ignore_errors=False):
        """
        Run loop to send notification when the offers changed.

        :param chat_ids: List of Integers, Telegram chat ids of the receivers.
        :param update_interval: Float, the seconds between refreshes. Default: 300
        :param initial: Boolean, whether to send a notification when starting the loop. Default: False
        :param ignore_errors: Boolean, set True to keep the loop running if any Exception is thrown. Default: False
        :param show_days: Boolean, False if the offers' dates should be given, True for day difference. Default: False
        """

        def offers_equal(offers1, offers2):
            set1, set2 = set(offers1), set(offers2)
            return len(set1 - set2) == len(set2 - set1) == 0

        print(f"Notifying {chat_ids} when offers change (refreshing every {update_interval} seconds).")

        self.update_offers()
        if initial:
            self.notify(chat_ids, show_days)

        last_offers = self.offers

        if ignore_errors:
            print("Ignoring errors.")
            while True:
                try:
                    sleep(update_interval)
                    self.update_offers()
                    if not offers_equal(last_offers, self.offers):
                        self.notify(chat_ids, show_days)
                        last_offers = self.offers
                except Exception as e:
                    print(f"Ignoring error: {e}")

        else:
            while True:
                sleep(update_interval)
                self.update_offers()
                if not offers_equal(last_offers, self.offers):
                    self.notify(chat_ids, show_days)
                    last_offers = self.offers
