import datetime as dt

import requests as req

URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"


class Offer:

    def __init__(self, title, start_date, end_date):
        self.title = title
        self.start_date = start_date
        self.end_date = end_date

    def format_offer(self, is_active, show_days):
        """Formats an offer into a string."""
        if is_active and show_days:
            date_string = f"{(self.end_date - dt.datetime.now()).days} days left"
        if is_active and not show_days:
            date_string = f"until {self.end_date.strftime('%d %b')}"
        if not is_active and show_days:
            date_string = f"in {(self.start_date - dt.datetime.now()).days} days"
        if not is_active and not show_days:
            date_string = f"from {self.start_date.strftime('%d %b')}"

        return date_string + f": \"{self.title}\""


def _perform_request(country):
    res = req.get(URL, params={"country": country})
    res.raise_for_status()
    return res.json()


def get_offers(country):
    # get offers
    res = _perform_request(country)
    elements = res["data"]["Catalog"]["searchStore"]["elements"]

    # get relevant fields
    out = []
    for e in elements:

        # if there is a promotion for e
        if e["promotions"]:

            # get dates
            if e["promotions"]["promotionalOffers"]:
                promo = e["promotions"]["promotionalOffers"][0]["promotionalOffers"][0]
            else:
                promo = e["promotions"]["upcomingPromotionalOffers"][0]["promotionalOffers"][0]

            start_date = dt.datetime.fromisoformat(promo["startDate"].split("Z")[0])
            end_date = dt.datetime.fromisoformat(promo["endDate"].split("Z")[0])

            out.append(Offer(e["title"], start_date, end_date))

    return out
