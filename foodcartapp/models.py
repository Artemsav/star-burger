from django.db import models
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import F, Sum
from django.utils import timezone


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='rest_items',
        verbose_name='ресторан',
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def count_order_price(self):
        order_items = self.annotate(item_price=Sum(F('order_items__quantity')*F('order_items__product__price'), distinct=True))
        return order_items


class Order(models.Model):
    address = models.CharField(
        'адрес',
        max_length=100
    )
    firstname = models.CharField(
        'Имя',
        max_length=50
    )
    lastname = models.CharField(
        'Фамилия',
        max_length=50
    )
    phonenumber = PhoneNumberField(region='RU')

    MANAGER = 'MN'

    RESTAURANT = 'REST'

    COURIER = 'CR'

    FINISHED = 'FN'

    STATUS_CHOICES = [
        (MANAGER, 'Необработано'),
        (RESTAURANT, 'В ресторане'),
        (COURIER, 'В доставке'),
        (FINISHED, 'Закрыт')
    ]

    status = models.CharField(
        max_length=4,
        choices=STATUS_CHOICES,
        default=MANAGER
    )

    comment = models.TextField(
        'Комментарий к заказу',
        max_length=200,
        blank=True,
        null=True
    )

    registered_at = models.DateTimeField(
        'Зарегистрирован',
        default=timezone.now,
        db_index=True
        )

    called_at = models.DateTimeField('Звонок', blank=True, null=True)

    delivered_at = models.DateTimeField('Доставлено', blank=True, null=True)

    ELECTRON_PAY = 'EP'

    CASH_PAY = 'CP'

    PAY_CHOICES = [
        (ELECTRON_PAY, 'Электронный платеж'),
        (CASH_PAY, 'Наличными'),
    ]

    pay_method = models.CharField(
        max_length=2,
        choices=PAY_CHOICES,
        default=CASH_PAY,
        db_index=True
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'{self.firstname} {self.lastname} {self.address}'


class OrderItem(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='продукт'
        )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='Заказ'
    )
    quantity = models.IntegerField('количество')

    price = models.DecimalField('Цена позиции', max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)

    class Meta:
        verbose_name = 'пункт меню заказа'
        verbose_name_plural = 'пункты меню заказов'
        unique_together = [
            ['product', 'order']
        ]

    def __str__(self):
        return f'{self.product.name} {self.quantity}'
