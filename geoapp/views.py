import requests
from geopy import distance


def get_distance(coordinates, restaurant_coordinates):
    lon, lat = coordinates
    restaurant_lan, restaurant_lot = restaurant_coordinates
    if lon and lat and restaurant_lan and restaurant_lot:
        return distance.distance(coordinates, restaurant_coordinates).km


def check_address(addresses, saved_addresses):
    check_result = []
    for address in addresses:
        if address in saved_addresses:
            continue
        else:
            check_result.append(address)
    return check_result


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat
