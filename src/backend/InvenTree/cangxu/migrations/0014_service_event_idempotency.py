from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('cangxu', '0013_purchase_receipt_packaging_barcode')]

    operations = [
        migrations.AddField(
            model_name='servicecaseevent',
            name='idempotency_key',
            field=models.UUIDField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='servicecaseevent',
            name='request_hash',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
    ]
