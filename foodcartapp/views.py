from django.http import JsonResponse
from django.templatetags.static import static
from django.db import transaction
from .models import Product, Order, OrderItem
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import ValidationError

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


class OrderItemSerializer(ModelSerializer):

    class Meta:
        model = OrderItem
        allow_empty = False
        fields = [
            'quantity',
            'product',
        ]


class OrderSerializer(ModelSerializer):
    products = OrderItemSerializer(many=True, write_only=True)

    def validate_products(self, value):
        if isinstance(value, list):
            if len(value) > 0:
                return value
        raise ValidationError('Products key not presented or not list')

    class Meta:
        model = Order
        allow_empty = False
        fields = [
            'address',
            'firstname',
            'lastname',
            'phonenumber',
            'products'
            ]


@transaction.atomic
@api_view(['POST'])
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    order = Order.objects.create(
            address=serializer.validated_data['address'],
            firstname=serializer.validated_data['firstname'],
            lastname=serializer.validated_data['lastname'],
            phonenumber=serializer.validated_data['phonenumber']
            )
    order_item_fields = serializer.validated_data['products']
    items = [
        OrderItem(
            order=order, **fields, price=fields['quantity']*fields['product'].price
            ) for fields in order_item_fields
        ]
    OrderItem.objects.bulk_create(items)
    if serializer.is_valid:
        return Response(serializer.data, status=status.HTTP_200_OK)
    return JsonResponse(serializer.errors, status=400)
