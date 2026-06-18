"""Migration to change NotificationMessage object_id fields from PositiveIntegerField to CharField.

This allows notifications to reference models that use non-integer primary keys,
such as UUIDField (e.g. MachineConfig), without a database overflow error.

See: https://github.com/inventree/InvenTree/issues/12131
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0043_auto_20260518_1206'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationmessage',
            name='target_object_id',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='notificationmessage',
            name='source_object_id',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
