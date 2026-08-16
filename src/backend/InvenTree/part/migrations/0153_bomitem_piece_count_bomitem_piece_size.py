"""Add piece_count field to BomItem model.

This field supports cut-to-length parts (cables, tubing, profiles) where
a BOM line requires multiple pieces of a specific size. The existing
quantity field represents the per-piece size/length, and piece_count
indicates how many pieces are needed. Total material = quantity x piece_count.
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
                help_text='Number of pieces required (for cut-to-length items). Total material = quantity x piece_count.',
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name='Piece Count',
            ),
        ),
    ]
