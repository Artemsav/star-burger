# Generated by Django 3.2 on 2022-08-16 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geoapp', '0004_auto_20220803_1111'),
    ]

    operations = [
        migrations.AlterField(
            model_name='addresscoordinates',
            name='lat',
            field=models.FloatField(default=None, null=True, verbose_name='Широта'),
        ),
        migrations.AlterField(
            model_name='addresscoordinates',
            name='lon',
            field=models.FloatField(default=None, null=True, verbose_name='Долгота'),
        ),
    ]
