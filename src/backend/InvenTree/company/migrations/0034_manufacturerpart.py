import InvenTree.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0033_auto_20210410_1528'),
    ]

    operations = [
        migrations.CreateModel(
            name='ManufacturerPart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('MPN', models.CharField(help_text='Manufacturer Part Number', max_length=100, null=True, verbose_name='MPN')),
                ('link', InvenTree.fields.InvenTreeURLField(blank=True, help_text='URL for external manufacturer part link', null=True, verbose_name='Link')),
                ('description', models.CharField(blank=True, help_text='Manufacturer part description', max_length=250, null=True, verbose_name='Description')),
                ('manufacturer', models.ForeignKey(help_text='Select manufacturer', limit_choices_to={'is_manufacturer': True}, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='manufactured_parts', to='company.Company', verbose_name='Manufacturer')),
                ('part', models.ForeignKey(help_text='Select part', limit_choices_to={'purchaseable': True}, on_delete=django.db.models.deletion.CASCADE, related_name='manufacturer_parts', to='part.Part', verbose_name='Base Part')),
            ],
            options={
                'unique_together': {('part', 'manufacturer', 'MPN')},
            },
        ),
    ]
