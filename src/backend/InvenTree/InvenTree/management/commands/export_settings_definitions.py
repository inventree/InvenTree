"""Custom management command to export settings definitions.

This is used to generate a JSON file which contains all of the settings,
so that they can be introspected by the InvenTree documentation system.

This in turn allows settings to be documented in the InvenTree documentation,
without having to manually duplicate the information in multiple places.
"""

import json

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Extract settings information, and export to a JSON file."""

    def add_arguments(self, parser):
        """Add custom arguments for this command."""
        parser.add_argument(
            'filename', type=str, help='Output filename for settings definitions'
        )

    def handle(self, *args, **kwargs):
        """Export settings information to a JSON file."""
        from common.models import InvenTreeSetting, InvenTreeUserSetting

        settings = {'global': {}, 'user': {}}

        # Global settings
        for key, setting in InvenTreeSetting.SETTINGS.items():
            settings['global'][key] = {
                'name': str(setting['name']),
                'description': str(setting['description']),
                'default': str(InvenTreeSetting.get_setting_default(key)),
                'units': str(setting.get('units', '')),
            }

        # User settings
        for key, setting in InvenTreeUserSetting.SETTINGS.items():
            settings['user'][key] = {
                'name': str(setting['name']),
                'description': str(setting['description']),
                'default': str(InvenTreeUserSetting.get_setting_default(key)),
                'units': str(setting.get('units', '')),
            }

        filename = kwargs.get('filename', 'inventree_settings.json')

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)

        print(f"Exported InvenTree settings definitions to '{filename}'")
