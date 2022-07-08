import re
from foodcartapp.models import OrderItem, Product, Restaurant, Order, RestaurantMenuItem
import requests
from geopy import distance
import os
from geoapp.models import AddressCoordinates


def get_distance(address, restaurant_address):
    try:
        return distance.distance(address, restaurant_address).km
    except ValueError:
        return 'Расстояние не определено'


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
        return 'Not found'
    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lat, lon
apikey = os.getenv('YANDEX_GEO')

orders_rests = {}
order_address = {}
saved_addresses = []
orders = list(Order.objects.prefetch_related('order_items__product').count_order_price())
rest_items = list(RestaurantMenuItem.objects.select_related('product').select_related('restaurant').filter(availability=True))
address_coordinates = AddressCoordinates.objects.all()
for addresses in address_coordinates:
    saved_addresses.append(addresses.address)
for restaurant in rest_items:
    restaurant_address = restaurant.restaurant.address
    if not set([restaurant_address]).issubset(saved_addresses):
        rest_lat, rest_lon = fetch_coordinates(apikey, restaurant_address)
        address_coordinates.create(address=restaurant_address,lat=rest_lat,lon=rest_lon)
for order in orders:
    restorans = []
    print(f'==This is order===={order}======')
    item_with_products = order.order_items.all()
    print(f'==This is order items===={item_with_products}======')
    product_restourant = []
    for item in item_with_products:
        product_restourant.append([rest.restaurant for rest in rest_items if rest.product.name==item.product.name])
    print(f'===This is resrourant list=====>{restorans}')
    print('==========order results===========')
    order_result = set(product_restourant[0]).intersection(*product_restourant)
    print(f'===Order results(intersections)======={order_result}===========')
    order_address = order.address
    if set([order_address]).issubset(saved_addresses):
        print('++++set work')
        orders_rests[order.id] = sorted([(rest.name, get_distance((address_coordinates.filter(address=rest.address)[0].lat, address_coordinates.filter(address=rest.address)[0].lon), (address_coordinates.filter(address=order.address)[0].lat, address_coordinates.filter(address=order.address)[0].lon))) for rest in order_result], key= lambda rest:rest[1]) 
    else:
        order_lat, order_lon = fetch_coordinates(apikey, order_address)
        address_coordinates.create(
            address=order_address,
            lat=order_lat,
            lon=order_lon
        )
        orders_rests[order.id] = sorted([(rest.name, get_distance((address_coordinates.filter(address=rest.address)[0].lat, address_coordinates.filter(address=rest.address)[0].lon), (order_lat, order_lon))) for rest in order_result], key=lambda rest:rest[1])
    print('+++++++++++Result dict to request++++++++++++++',orders_rests)
