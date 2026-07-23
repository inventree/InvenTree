"""Add piece_count and piece_size fields to BomItem model.

These fields support cut-to-length parts (cables, tubing, profiles) where
a BOM line requires multiple pieces of a specific size, rather than a
single total quantity.
"""

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('part', '0152_alter_partpricing_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='bomitem',
            name='piece_count',
            field=models.PositiveIntegerField(
                default=1,
                help_text='Number of pieces required (for cut-to-length items)',
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name='Piece Count',
            ),
        ),
        migrations.AddField(
            model_name='bomitem',
            name='piece_size',
            field=models.CharField(
                blank=True,
                help_text='Size of each piece (e.g. "250 mm"). When specified, total quantity = piece_count × piece_size.',
                max_length=25,
                verbose_name='Piece Size',
            ),
        ),
    ]
