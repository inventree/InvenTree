import InvenTree.fields
from django.db import migrations, models
import django.db.models.deletion

def supplierpart_make_manufacturer_parts(apps, schema_editor):
    Part = apps.get_model('part', 'Part')
    ManufacturerPart = apps.get_model('company', 'ManufacturerPart')
    SupplierPart = apps.get_model('company', 'SupplierPart')
    
    print(f'\nCreating Manufacturer parts\n{"-"*10}')
    for supplier_part in SupplierPart.objects.all():
        print(f'{supplier_part.supplier.name[:15].ljust(15)} | {supplier_part.SKU[:15].ljust(15)}\t', end='')

        if supplier_part.manufacturer_part:
            print(f'[ERROR: MANUFACTURER PART ALREADY EXISTS]')
            continue

        part = supplier_part.part
        if not part:
            print(f'[ERROR: SUPPLIER PART IS NOT CONNECTED TO PART]')
            continue
        
        manufacturer = supplier_part.manufacturer
        MPN = supplier_part.MPN
        link = supplier_part.link
        description = supplier_part.description

        if manufacturer or MPN:
            print(f' | {part.name[:15].ljust(15)}', end='')
            
            try:
                print(f' | {manufacturer.name[:15].ljust(15)}', end='')
            except TypeError:
                print(f' | {"EMPTY MANUF".ljust(15)}', end='')

            try:
                print(f' | {MPN[:15].ljust(15)}', end='')
            except TypeError:
                print(f' | {"EMPTY MPN".ljust(15)}', end='')

            print('\t', end='')

            # Create ManufacturerPart
            manufacturer_part = ManufacturerPart(part=part, manufacturer=manufacturer, MPN=MPN, link=link, description=description)
            manufacturer_part.save()

            # Link it to SupplierPart
            supplier_part.manufacturer_part = manufacturer_part
            supplier_part.save()

            print(f'[SUCCESS: MANUFACTURER PART CREATED]')
        else:
            print(f'[IGNORED: MISSING MANUFACTURER DATA]')

    print(f'{"-"*10}\nDone')


class Migration(migrations.Migration):

    dependencies = [
        ('part', '0063_bomitem_inherited'),
        ('company', '0031_auto_20210103_2215'),
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
        migrations.AddField(
            model_name='supplierpart',
            name='manufacturer_part',
            field=models.ForeignKey(blank=True, help_text='Select manufacturer part', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='supplier_parts', to='company.ManufacturerPart', verbose_name='Manufacturer Part'),
        ),
        # Make new ManufacturerPart with SupplierPart "manufacturer" and "MPN"
        # fields, then link it to the new SupplierPart "manufacturer_part" field
        migrations.RunPython(supplierpart_make_manufacturer_parts),
        migrations.RemoveField(
            model_name='supplierpart',
            name='MPN',
        ),
        migrations.RemoveField(
            model_name='supplierpart',
            name='manufacturer',
        ),
    ]
