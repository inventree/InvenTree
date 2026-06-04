from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('company', '0036_supplierpart_update_2')]

    operations = [
        migrations.RemoveField(model_name='supplierpart', name='MPN'),
        migrations.RemoveField(model_name='supplierpart', name='manufacturer'),
    ]
