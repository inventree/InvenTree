"""Initial migration for the 'scim' app."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Create the singleton ScimConfiguration model."""

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ScimConfiguration',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'enabled',
                    models.BooleanField(
                        default=False,
                        help_text='Enable the SCIM provisioning endpoint',
                        verbose_name='Enabled',
                    ),
                ),
                (
                    'secret_digest',
                    models.CharField(
                        blank=True,
                        help_text='HMAC digest of the current SCIM bearer secret',
                        max_length=64,
                        verbose_name='Secret Digest',
                    ),
                ),
                (
                    'secret_generated',
                    models.DateTimeField(
                        blank=True, null=True, verbose_name='Secret Generated'
                    ),
                ),
                (
                    'last_used',
                    models.DateTimeField(
                        blank=True, null=True, verbose_name='Last Used'
                    ),
                ),
            ],
            options={'verbose_name': 'SCIM Configuration'},
        )
    ]
