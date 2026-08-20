# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("importer", "0005_dataimportsession_update_records"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataimportcolumnmap",
            name="lookup_field",
            field=models.CharField(
                blank=True,
                null=True,
                max_length=100,
                verbose_name="Lookup Field",
                help_text="Database field to use for foreign-key lookup. Leave blank for automatic lookup.",
            ),
        ),
    ]
