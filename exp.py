from foodcartapp.models import OrderItem, Product, Restaurant, Order, RestaurantMenuItem
orders_rest = {}
orders = Order.objects.count_order_price()
rest_items = RestaurantMenuItem.objects.all().select_related('restaurant').select_related('product')
for order in orders:
    restorans = []
    print(f'======{order}======')
    item_with_products = order.order_items.all()
    print(f'======{item_with_products}======')
    for order_item in item_with_products:
        product_id = order_item.product.id
        restoran_menu_item = rest_items.filter(product__id=product_id).filter(availability=True)
        restorans.append([rest.restaurant.name for rest in restoran_menu_item])
    print(f'========>{restorans}')
    print('==========order results===========')
    order_result = set(restorans[0]).intersection(*restorans)
    print(order_result)
    orders_rest[order.id]=order_result
