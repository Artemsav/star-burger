from django.db import models
from django.utils import timezone


class AddressCoordinates(models.Model):
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
        unique=True
    )
    lat = models.FloatField(verbose_name='Широта')
    lon = models.FloatField(verbose_name='Долгота')
    registered_at = models.DateTimeField(
        'Зарегистрирован',
        default=timezone.now,
        db_index=True
        )

    def __str__(self):
        return self.address
