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


orders_rests = {}
order_address = {}
a = {}
apikey = os.getenv('YANDEX_GEO')
orders = Order.objects.count_order_price()
rest_items = RestaurantMenuItem.objects.all().select_related('restaurant').select_related('product')
address_coordinates = AddressCoordinates.objects.all()
for order in orders:
    restorans = []
    print(f'======{order}======')
    item_with_products = order.order_items.all()
    print(f'======{item_with_products}======')
    for order_item in item_with_products:
        product_id = order_item.product.id
        restoran_menu_item = rest_items.filter(product__id=product_id).filter(availability=True)
        restorans.append([rest.restaurant for rest in restoran_menu_item])
    print(f'========>{restorans}')
    print('==========order results===========')
    order_result = set(restorans[0]).intersection(*restorans)
    print(f'=========={order_result}===========')
    print(order.address)
    order_address = order.address
    if not address_coordinates.filter(address=order_address):
        order_address = order.address
        order_lat, order_lon = fetch_coordinates(apikey, order_address)
        address_coordinates.create(
            address=order_address,
            lat=order_lat,
            lon=order_lon
        )
    for rest in order_result:
        rest_address = rest.address
        if not address_coordinates.filter(address=rest_address):
            try:
                rest_lat, rest_lon = fetch_coordinates(apikey, rest_address)
                address_coordinates.create(
                    address=rest_address,
                    lat=rest_lat,
                    lon=rest_lon
                )
            except ValueError:
                None
    orders_rests[order.id] = sorted([(rest.name, get_distance((address_coordinates.filter(address=order.address)[0].lat,address_coordinates.filter(address=order.address)[0].lon,), fetch_coordinates(apikey, order.address))) for rest in order_result], key= lambda rest:rest[1])
    print('________________',orders_rests)
