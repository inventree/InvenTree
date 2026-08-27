# Generated migration: Add part field to RepairOrder

import django.db.models.deletion
from django.utils.translation import gettext_lazy as _

from django.db import migrations, models


class Migration(migrations.Migration):
    """Add optional part ForeignKey to RepairOrder.

    This allows a repair order to be scoped to a specific Part,
    enabling filtering and reporting by part.
    """

    dependencies = [
        ('build', '0060_repairorder_repairorderlineitem_and_more'),
        ('part', '0153_bomitem_piece_count_bomitem_piece_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='repairorder',
            name='part',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='repair_orders',
                to='part.part',
                verbose_name='Part',
                help_text='Part associated with this repair order',
            ),
        )
    ]
