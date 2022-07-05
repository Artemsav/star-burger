from foodcartapp.models import OrderItem, Product, Restaurant, Order, RestaurantMenuItem
orders_rests = {}
order_distance = {}
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
    orders_rests[order.id] = order_result
    order_distance[order.id] = [rest_items.restaurant.filter(name=rest_name)[0].address for rest_name in order_result]