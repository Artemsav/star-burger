from django.http import JsonResponse
from django.templatetags.static import static
import json

from .models import Product, Order, OrderItem
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    response = request.data
    if isinstance(response.get('products'), list):
        if len(response.get('products')) > 0:
            order = Order.objects.create(
                address=response.get('address'),
                name=response.get('firstname'),
                surname=response.get('lastname'),
                phone_number=response.get('phonenumber')
                )
            products = Product.objects.all()
            for item in response.get('products'):
                OrderItem.objects.create(
                    order=order,
                    quantity=item.get('quantity'),
                    product=products.get(id=item.get('product'))
                )
            print(response)
            return Response(response)
        else:
            content = {'data Erorr': 'products key not presented or not list'}
            return Response(content, status=status.HTTP_200_OK)
    else:
        content = {'data Erorr': 'products key not presented or not list'}
        return Response(content, status=status.HTTP_200_OK)
