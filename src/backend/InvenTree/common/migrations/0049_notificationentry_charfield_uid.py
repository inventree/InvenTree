"""Allow notification entries to reference UUID primary keys."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0048_notificationmessage_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationentry',
            name='uid',
            field=models.CharField(max_length=255),
        ),
    ]
