import InvenTree.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0036_supplierpart_update_2'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='supplierpart',
            name='MPN',
        ),
        migrations.RemoveField(
            model_name='supplierpart',
            name='manufacturer',
        ),
    ]
