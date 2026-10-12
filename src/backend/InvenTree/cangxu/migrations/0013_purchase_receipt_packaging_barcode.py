from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('cangxu', '0012_purchase_receipt_idempotency')]

    operations = [
        migrations.AddField(
            model_name='purchasereceipt',
            name='packaging',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='purchasereceipt',
            name='barcode',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
