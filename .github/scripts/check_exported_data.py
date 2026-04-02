"""Script to check a data file exported using the 'export-records' command.

This script is intended to be used as part of the CI workflow,
in conjunction with the "workflows/import_export.yaml" workflow.

In reads the exported data file, to ensure that:

- The file can be read and parsed as JSON
- The file contains the expected metadata
- The file contains the expected plugin configuration
- The file contains the expected plugin database records

"""

PLUGIN_KEY = 'dummy_app_plugin'
PLUGIN_SLUG = 'dummy-app-plugin'

import argparse
import json
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check exported data file')
    parser.add_argument('datafile', help='Path to the exported data file (JSON)')

    args = parser.parse_args()

    if not os.path.isfile(args.datafile):
        print(f'Error: File not found: {args.datafile}')
        exit(1)

    with open(args.datafile, encoding='utf-8') as f:
        try:
            data = json.load(f)
            print(f'Successfully loaded data from {args.datafile}')
            print(f'Number of records: {len(data)}')
        except json.JSONDecodeError as e:
            print(f'Error: Failed to parse JSON file: {e}')
            exit(1)

    found_metadata = False
    found_installed_apps = False
    found_plugin_config = False
    plugin_data_records = {}

    # Inspect the data and check that it has the expected structure and content.
    for entry in data:
        # Check metadata entry for expected values
        if entry.get('metadata', False):
            print('Found metadata entry')
            found_metadata = True

            expected_apps = ['InvenTree', 'allauth', 'dbbackup', PLUGIN_KEY]

            apps = entry.get('installed_apps', [])

            for app in expected_apps:
                if app not in apps:
                    print(f'- Expected app "{app}" not found in installed apps list')
                    exit(1)

            found_installed_apps = True

        elif entry.get('model', None) == 'plugin.pluginconfig':
            key = entry['fields']['key']

            if key == PLUGIN_SLUG:
                print(f'Found plugin configuration for plugin "{PLUGIN_KEY}"')
                found_plugin_config = True

        elif entry.get('model', None) == f'{PLUGIN_KEY}.examplemodel':
            key = entry['fields']['key']
            value = entry['fields']['value']

            plugin_data_records[key] = value

    if not found_metadata:
        print('Error: No metadata entry found in exported data')
        exit(1)

    if not found_installed_apps:
        print(
            f'Error: Plugin "{PLUGIN_KEY}" not found in installed apps list in metadata'
        )
        exit(1)

    if not found_plugin_config:
        print(f'Error: No plugin configuration found for plugin "{PLUGIN_KEY}"')
        exit(1)

    # Check the extracted plugin records
    expected_keys = ['alpha', 'beta', 'gamma', 'delta']

    for key in expected_keys:
        if key not in plugin_data_records:
            print(
                f'Error: Expected plugin record with key "{key}" not found in exported data'
            )
            exit(1)

    print('All checks passed successfully!')
