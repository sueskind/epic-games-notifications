import datetime as dt
from time import sleep

import requests as req
import schedule

from . import epic

TELEGRAM_SEND_URL_FMT = "https://api.telegram.org/bot{}/sendMessage"


def _format_offer(offer, is_active, show_days):
    """Formats an offer into a string."""
    if is_active and show_days:
        date_string = f"{(offer['end_date'] - dt.datetime.now()).days} days left"
    if is_active and not show_days:
        date_string = f"until {offer['end_date'].strftime('%d %b')}"
    if not is_active and show_days:
        date_string = f"in {(offer['start_date'] - dt.datetime.now()).days} days"
    if not is_active and not show_days:
        date_string = f"from {offer['start_date'].strftime('%d %b')}"

    return date_string + f": \"{offer['title']}\""


def _escaped_string(s):
    """Replaces characters in a string for Markdown V2."""
    for c in "_*[]()~>#+-=|{}.!":
        s = s.replace(c, "\\" + c)
    return s


class Notifier:

    def __init__(self, bot_token, country="US"):
        self.bot_token = bot_token
        self.country = country
        self.offers = None

    def update_offers(self):
        self.offers = epic.offers(self.country)

    def notify(self, chat_id, show_days=False):
        """
        Gets the current offers and sends a Telegram notification.

        :param chat_id: Integer, Telegram chat id of the receiver.
        :param show_days: Boolean, False if the offers' dates should be given, True for day difference. Default: False
        """

        if not self.offers:
            raise AttributeError("No offers registered. Did you run 'update_offers'?")

        current, upcoming = [], []
        for o in self.offers:
            if o["start_date"] < dt.datetime.now():
                current.append(o)
            else:
                upcoming.append(o)

        current = "\n".join(_format_offer(o, True, show_days) for o in current)
        upcoming = "\n".join(_format_offer(o, False, show_days) for o in upcoming)

        message = f"Current:\n{current}\n\nUpcoming:\n{upcoming}"

        params = {
            "chat_id": chat_id,
            "text": message
        }

        res = req.get(TELEGRAM_SEND_URL_FMT.format(self.bot_token), params=params)
        res.raise_for_status()

    def notify_weekly(self, chat_id, dow, time, show_days=False, ignore_errors=False):
        """
        Run loop to send notification weekly on a given day of week.

        :param chat_id: Integer, Telegram chat id of the receiver.
        :param dow: Integer, 0 = Monday, 1 = Tuesday, ..., 6 = Sunday
        :param time: String, clock time for the notification. Format: HH:MM
        :param ignore_errors: Boolean, set True to keep the loop running if any Exception is thrown. Default: False
        :param show_days: Boolean, False if the offers' dates should be given, True for day difference. Default: False
        """

        def job():
            self.update_offers()
            self.notify(chat_id, show_days)

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

        print(f"Notifying {chat_id} every {day_name} at {time}.")

        if ignore_errors:
            print("Ignoring errors.")
            while True:
                try:
                    schedule.run_pending()
                except Exception:
                    pass
                sleep(1)

        else:
            while True:
                schedule.run_pending()
                sleep(1)

    def notify_on_change(self, chat_id, update_interval=300, initial=False, show_days=False, ignore_errors=False):
        """
        Run loop to send notification when the offers changed.

        :param chat_id: Integer, Telegram chat id of the receiver.
        :param update_interval: Float, the seconds between refreshes. Default: 300
        :param initial: Boolean, whether to send a notification when starting the loop. Default: False
        :param ignore_errors: Boolean, set True to keep the loop running if any Exception is thrown. Default: False
        :param show_days: Boolean, False if the offers' dates should be given, True for day difference. Default: False
        """

        print(f"Notifying {chat_id} when offers change (refreshing every {update_interval} seconds).")

        self.update_offers()
        if initial:
            self.notify(chat_id, show_days)

        last_offers = self.offers

        if ignore_errors:
            print("Ignoring errors.")
            while True:
                try:
                    sleep(update_interval)
                    self.update_offers()
                    if last_offers != self.offers:
                        self.notify(chat_id, show_days)
                        last_offers = self.offers
                except Exception:
                    pass

        else:
            while True:
                sleep(update_interval)
                self.update_offers()
                if last_offers != self.offers:
                    self.notify(chat_id, show_days)
                    last_offers = self.offers
