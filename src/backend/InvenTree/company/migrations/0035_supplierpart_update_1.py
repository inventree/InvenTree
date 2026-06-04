import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('company', '0034_manufacturerpart')]

    operations = [
        migrations.AddField(
            model_name='supplierpart',
            name='manufacturer_part',
            field=models.ForeignKey(
                blank=True,
                help_text='Select manufacturer part',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='supplier_parts',
                to='company.ManufacturerPart',
                verbose_name='Manufacturer Part',
            ),
        )
    ]
