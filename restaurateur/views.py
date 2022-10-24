from contextlib import suppress

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from geoapp.exceptions import CoordinatesNotFound
from foodcartapp.models import Order, Product, Restaurant
from geoapp.models import AddressCoordinates
from geoapp.views import get_distance, fetch_coordinates


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

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
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
    new_addresses = []
    orders = list(
        Order.objects
        .prefetch_related('items__product')
        .select_related('assigned_restaurant')
        .order_by('status')
        .count_order_price()
        .get_available_restaurant()
        )
    restaurants = Restaurant.objects.all()
    order_addresses = [order.address for order in orders]
    restaurant_addresses = [restaurant.address for restaurant in restaurants]
    addresses_to_check = order_addresses + restaurant_addresses
    address_coordinates = AddressCoordinates.objects.filter(address__in=addresses_to_check)
    saved_addresses = {address.address: (address.lon, address.lat) for address in address_coordinates}
    for address in addresses_to_check:
        if address in saved_addresses.keys():
            continue
        else:
            order_lat, order_lon = None, None
            with suppress(CoordinatesNotFound):
                order_lat, order_lon = fetch_coordinates(apikey, address)
            new_addresses.append(AddressCoordinates(
                address=address,
                lat=order_lat,
                lon=order_lon))
    if new_addresses:
        address_coordinates.bulk_create(new_addresses)
    for order in orders:
        order_available_restaurants = order.available_restaurants
        order.restaurants = [
            (
                restaurant.name,
                get_distance(
                    saved_addresses[order.address],
                    saved_addresses[restaurant.address]
                    )
                ) for restaurant in order_available_restaurants
            ]
    return render(request, template_name='order_items.html', context={
        'orders': orders,
    })
