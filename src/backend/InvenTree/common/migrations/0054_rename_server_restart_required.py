"""Remove the legacy 'SERVER_RESTART_REQUIRED' setting.

The flag has been renamed to '_SERVER_RESTART_REQUIRED' (internal setting),
so that it is not exposed via the settings API.

The value does not need to be migrated: the flag is cleared on every server
start, and applying this migration implies a server restart.
"""

from django.db import migrations


def remove_legacy_restart_flag(apps, schema_editor):
    """Delete any stored 'SERVER_RESTART_REQUIRED' setting."""
    InvenTreeSetting = apps.get_model('common', 'InvenTreeSetting')
    InvenTreeSetting.objects.filter(key='SERVER_RESTART_REQUIRED').delete()


class Migration(migrations.Migration):
    """Remove the legacy SERVER_RESTART_REQUIRED setting."""

    dependencies = [
        ('common', '0053_inventreesetting_touched_inventreesetting_updated_and_more')
    ]

    operations = [
        migrations.RunPython(
            remove_legacy_restart_flag, reverse_code=migrations.RunPython.noop
        )
    ]
