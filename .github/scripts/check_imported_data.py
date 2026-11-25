"""Script to check the database state after an 'import-records --exclude-plugins' run.

This script is intended to be used as part of the CI workflow,
in conjunction with the "workflows/import_export.yaml" workflow
(see the 'exclude-plugins' job).

It checks that:

- Core data (e.g. Part records) was imported
- No plugin configuration was imported for the dummy plugin

Intended to be run from 'src/backend/InvenTree', e.g.:
    cd src/backend/InvenTree && python ../../../.github/scripts/check_imported_data.py
"""

import os
import sys

sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InvenTree.settings')

import django

django.setup()

from part.models import Part
from plugin.models import PluginConfig, PluginSetting

PLUGIN_SLUG = 'dummy-app-plugin'

if __name__ == '__main__':
    part_count = Part.objects.count()

    if part_count == 0:
        print('Error: Expected core Part data to be imported, but none was found')
        sys.exit(1)

    print(f'Confirmed {part_count} Part record(s) imported')

    if PluginConfig.objects.filter(key=PLUGIN_SLUG).exists():
        print(
            f'Error: Plugin configuration for "{PLUGIN_SLUG}" was imported, but should have been excluded'
        )
        sys.exit(1)

    if PluginSetting.objects.filter(plugin__key=PLUGIN_SLUG).exists():
        print(
            f'Error: Plugin settings for "{PLUGIN_SLUG}" were imported, but should have been excluded'
        )
        sys.exit(1)

    print(f'Confirmed no plugin data was imported for "{PLUGIN_SLUG}"')
    print('All checks passed successfully!')
