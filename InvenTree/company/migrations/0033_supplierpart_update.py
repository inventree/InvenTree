import InvenTree.fields
from django.db import migrations, models, transaction
import django.db.models.deletion
from django.db.utils import IntegrityError

def supplierpart_make_manufacturer_parts(apps, schema_editor):
    Part = apps.get_model('part', 'Part')
    ManufacturerPart = apps.get_model('company', 'ManufacturerPart')
    SupplierPart = apps.get_model('company', 'SupplierPart')

    supplier_parts = SupplierPart.objects.all()
    
    if supplier_parts:
        print(f'\nCreating Manufacturer parts\n{"-"*10}')
        for supplier_part in supplier_parts:
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
                except AttributeError:
                    print(f' | {"EMPTY MANUF".ljust(15)}', end='')

                try:
                    print(f' | {MPN[:15].ljust(15)}', end='')
                except TypeError:
                    print(f' | {"EMPTY MPN".ljust(15)}', end='')

                print('\t', end='')

                # Create ManufacturerPart
                manufacturer_part = ManufacturerPart(part=part, manufacturer=manufacturer, MPN=MPN, description=description, link=link)
                created = False
                try:
                    with transaction.atomic():
                        manufacturer_part.save()
                    created = True
                except IntegrityError:
                    manufacturer_part = ManufacturerPart.objects.get(part=part, manufacturer=manufacturer, MPN=MPN)

                # Link it to SupplierPart
                supplier_part.manufacturer_part = manufacturer_part
                supplier_part.save()

                if created:
                    print(f'[SUCCESS: MANUFACTURER PART CREATED]')
                else:
                    print(f'[IGNORED: MANUFACTURER PART ALREADY EXISTS]')
            else:
                print(f'[IGNORED: MISSING MANUFACTURER DATA]')

        print(f'{"-"*10}\nDone\n')


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0032_manufacturerpart'),
    ]

    operations = [
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
