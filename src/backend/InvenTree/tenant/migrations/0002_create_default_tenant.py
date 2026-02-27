from django.db import migrations


def create_default_tenant(apps, schema_editor):
    Tenant = apps.get_model('tenant', 'Tenant')

    if not Tenant.objects.filter(id=1).exists():
        Tenant.objects.create(
            id=1,
            name="Default Tenant"
        )


class Migration(migrations.Migration):

    dependencies = [
        ('tenant', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_tenant),
    ]