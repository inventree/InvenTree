# Generated manually to resolve CI missing migration error
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('build', '0061_repairorder_fields_and_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='repairorderallocation',
            name='quantity',
            field=models.DecimalField(decimal_places=5, default=1, max_digits=15, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='repairorderlineitem',
            name='quantity',
            field=models.DecimalField(decimal_places=5, default=1, max_digits=15, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]