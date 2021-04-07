import datetime as dt

import requests as req

from . import epic

TELEGRAM_SEND_URL_FMT = "https://api.telegram.org/bot{}/sendMessage"


def _format_offer(offer):
    return "{} ({} - {})".format(
        offer["title"],
        offer["start_date"].strftime("%Y-%m-%d"),
        offer["end_date"].strftime("%Y-%m-%d")
    )


def _escaped_string(s):
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

    def notify(self, chat_id):
        if not self.offers:
            raise AttributeError("No offers registered. Did you run 'update_offers'?")

        current, upcoming = [], []
        for o in self.offers:
            if o["start_date"] < dt.datetime.now():
                current.append(o)
            else:
                upcoming.append(o)

        current = "\n".join(_format_offer(o) for o in current)
        upcoming = "\n".join(_format_offer(o) for o in upcoming)

        message = f"Current:\n{current}\n\nUpcoming:\n{upcoming}"

        params = {
            "chat_id": chat_id,
            "text": message
        }

        res = req.get(TELEGRAM_SEND_URL_FMT.format(self.bot_token), params=params)
        res.raise_for_status()
