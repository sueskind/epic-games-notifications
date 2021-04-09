import datetime as dt

import requests as req

from . import epic

TELEGRAM_SEND_URL_FMT = "https://api.telegram.org/bot{}/sendMessage"


def _format_offer(offer, is_active, days=False):
    """Formats an offer into a string."""
    if is_active:
        return "until {}: \"{}\"".format(
            offer["end_date"].strftime("%d %b"),
            offer["title"])
    else:
        return "from {}: \"{}\"".format(
            offer["start_date"].strftime("%d %b"),
            offer["title"])


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

    def notify(self, chat_id, days=False):
        """
        Gets the current offers and sends a Telegram notification.

        :param chat_id: Integer, Telegram chat id of the receiver.
        :param days: Boolean, False if the offers' dates should be given, True for day difference. Default: False
        """

        if not self.offers:
            raise AttributeError("No offers registered. Did you run 'update_offers'?")

        current, upcoming = [], []
        for o in self.offers:
            if o["start_date"] < dt.datetime.now():
                current.append(o)
            else:
                upcoming.append(o)

        current = "\n".join(_format_offer(o, True) for o in current)
        upcoming = "\n".join(_format_offer(o, False) for o in upcoming)

        message = f"Current:\n{current}\n\nUpcoming:\n{upcoming}"

        params = {
            "chat_id": chat_id,
            "text": message
        }

        res = req.get(TELEGRAM_SEND_URL_FMT.format(self.bot_token), params=params)
        res.raise_for_status()
