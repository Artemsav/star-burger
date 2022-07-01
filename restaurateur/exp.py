from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from django.db.models import Prefetch
from foodcartapp.models import OrderItem, Product, Restaurant, Order, RestaurantMenuItem



order_items = Order.objects.count_order_price()
rest_items = RestaurantMenuItem.objects.all().select_related('restaurant').select_related('product')

for items in order_items:
    item_with_products = items.order_items.all()
    for product_id in item_with_products.product.id:
        rest_items.produ