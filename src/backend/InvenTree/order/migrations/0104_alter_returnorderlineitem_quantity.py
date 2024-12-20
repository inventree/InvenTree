# Generated by Django 4.2.16 on 2024-11-29 00:37

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0103_alter_salesorderallocation_shipment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='returnorderlineitem',
            name='quantity',
            field=models.DecimalField(decimal_places=5, default=1, help_text='Quantity to return', max_digits=15, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Quantity'),
        ),
    ]
