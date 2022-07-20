import requests
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.template.defaulttags import register
from django.urls import reverse_lazy
from django.views import View
from geopy import distance

from foodcartapp.models import Order, Product, Restaurant, RestaurantMenuItem
from geoapp.models import AddressCoordinates


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


def get_distance(address, restaurant_address):
    return distance.distance(address, restaurant_address).km


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


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:

        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
        }
        orderer_availability = [availability[restaurant.id] for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    apikey = settings.YANDEX_GEO
    orders_rests = {}
    new_order_addreses = []
    orders = list(
        Order.objects \
            .prefetch_related('items__product').select_related('assigned_restaurant') \
            .count_order_price().order_by('status')
                )
    rest_items = list(RestaurantMenuItem.objects.select_related('product') \
                    .select_related('restaurant').filter(availability=True))
    address_coordinates = AddressCoordinates.objects.all()
    saved_addresses = {addresses.address: (addresses.lon, addresses.lat) for addresses in address_coordinates}
    restaurants = Restaurant.objects.all()
    for restaurant in restaurants:
        restaurant_address = restaurant.address
        if restaurant_address not in saved_addresses:
            rest_lat, rest_lon = fetch_coordinates(apikey, restaurant_address)
            address_coordinates.create(
                address=restaurant_address,
                lat=rest_lat,
                lon=rest_lon
                )
    for order in orders:
        item_with_products = order.items.all()
        product_restaurants = []
        for item in item_with_products:
            product_restaurants.append(
                [
                    rest_item.restaurant for rest_item in rest_items \
                        if rest_item.product.name == item.product.name
                    ]
                )
        order_result = set(product_restaurants[0]).intersection(*product_restaurants)
        order_address = order.address
        if order_address in saved_addresses.keys():
            orders_rests[order.id] = [
                (
                    rest.name,
                    get_distance(
                        saved_addresses[rest.address],
                        saved_addresses[order.address]
                        )
                    ) for rest in order_result
                ]
        else:
            order_lat, order_lon = fetch_coordinates(apikey, order_address)
            new_order_addreses.append(AddressCoordinates(
                address=order_address,
                lat=order_lat,
                lon=order_lon
            ))
    if new_order_addreses:
        address_coordinates.bulk_create(new_order_addreses)
    return render(request, template_name='order_items.html', context={
        'orders': orders,
        'order_restaurants': orders_rests,
    })
