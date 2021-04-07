import requests as req

URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"


def _perform_request(country):
    res = req.get(URL, params={"country": country})
    res.raise_for_status()
    return res.json()


def get_games(country):
    res = _perform_request(country)

    print(res)


if __name__ == '__main__':
    get_games("DE")
