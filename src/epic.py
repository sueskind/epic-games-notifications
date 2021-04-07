import datetime as dt

import requests as req

URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"


def _perform_request(country):
    res = req.get(URL, params={"country": country})
    res.raise_for_status()
    return res.json()


def get_games(country):
    # get offers
    res = _perform_request(country)
    elements = res["data"]["Catalog"]["searchStore"]["elements"]

    # get relevant fields
    offers = []
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

            offers.append({"title": e["title"],
                           "start_date": start_date,
                           "end_date": end_date})

    return offers
