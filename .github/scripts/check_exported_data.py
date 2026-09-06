"""Script to check a data file exported using the 'export-records' command.

This script is intended to be used as part of the CI workflow,
in conjunction with the "workflows/import_export.yaml" workflow.

In reads the exported data file, to ensure that:

- The file can be read and parsed as JSON
- The file contains the expected metadata
- The file contains the expected plugin configuration
- The file contains the expected plugin database records

It can also optionally check the presence / absence of several categories of
data which 'export-records' can include or exclude via --include-x /
--exclude-x flags (email logs, API tokens, SSO app/token data, user sessions,
and non-empty group/user permissions) - pass e.g. '--check-email include' or
'--check-email exclude' to assert that category was (or was not) found in the
exported data. Any '--check-x' option which is *not* passed is simply not
checked at all (not even implicitly assumed absent) - so existing invocations
which don't pass any of them keep working unchanged.
"""

PLUGIN_KEY = 'dummy_app_plugin'
PLUGIN_SLUG = 'dummy-app-plugin'

import argparse
import json
import os


def check_category(
    data: list[dict], label: str, model_names: list[str], expect: str | None
):
    """Check that all of the given model names are present / absent as expected.

    Arguments:
        data: The loaded (parsed) exported data file.
        label: A human-readable label for this category, for error messages.
        model_names: The Django model labels (e.g. 'common.emailmessage')
            which make up this category.
        expect: 'include' - at least one entry for *each* model name must be
            present. 'exclude' - *no* entry for *any* model name may be
            present. None - this category was not requested to be checked;
            do nothing.
    """
    if expect is None:
        return

    expect_present = expect == 'include'

    counts = dict.fromkeys(model_names, 0)

    for entry in data:
        model = entry.get('model', None)
        if model in counts:
            counts[model] += 1

    if expect_present:
        for model, count in counts.items():
            if count == 0:
                print(f"Error: Expected '{label}' data ('{model}') was not found")
                exit(1)
        print(f"Found expected '{label}' data ({counts})")
    else:
        for model, count in counts.items():
            if count > 0:
                print(
                    f"Error: '{label}' data ('{model}') was found, but should have been excluded ({count} record(s))"
                )
                exit(1)
        print(f"Confirmed '{label}' data was correctly excluded")


def check_permissions(data: list[dict], expect: str | None):
    """Check that auth.group / auth.user permission fields are stripped or preserved as expected.

    Arguments:
        data: The loaded (parsed) exported data file.
        expect: 'include' - at least one auth.group / auth.user entry must
            have non-empty permissions. 'exclude' - all such entries must have
            empty permissions. None - not checked; do nothing.
    """
    if expect is None:
        return

    expect_present = expect == 'include'

    group_perms = [
        entry['fields'].get('permissions', [])
        for entry in data
        if entry.get('model') == 'auth.group'
    ]
    user_perms = [
        entry['fields'].get('user_permissions', [])
        for entry in data
        if entry.get('model') == 'auth.user'
    ]

    any_group_perms = any(group_perms)
    any_user_perms = any(user_perms)

    if expect_present:
        if not any_group_perms and not any_user_perms:
            print(
                'Error: Expected at least one auth.group / auth.user entry with '
                'non-empty permissions, but all were empty'
            )
            exit(1)
        print('Found expected non-empty group/user permissions')
    else:
        if any_group_perms or any_user_perms:
            print(
                'Error: Found non-empty group/user permissions, but they should '
                'have been stripped'
            )
            exit(1)
        print('Confirmed group/user permissions were correctly stripped')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check exported data file')
    parser.add_argument('datafile', help='Path to the exported data file (JSON)')

    # Plugin data is checked unconditionally below (it always has been) - this
    # just controls which direction is expected, mirroring export-records' own
    # --exclude-plugins flag (plugin data is included by default).
    parser.add_argument('--exclude-plugins', action='store_true')

    # The remaining categories are only checked when explicitly requested -
    # pass 'include' or 'exclude' to assert that direction, or omit the flag
    # entirely to skip checking that category (the default, for backwards
    # compatibility with existing invocations that don't pass any of these).
    for flag in ('email', 'tokens', 'sso', 'session', 'permissions'):
        parser.add_argument(f'--check-{flag}', choices=['include', 'exclude'])

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

    # Plugin data is included by default (export-records only excludes it when
    # given --exclude-plugins), so preserve that as the default expectation here
    if not args.exclude_plugins:
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
    elif found_plugin_config or plugin_data_records:
        print('Error: Plugin data was found, but should have been excluded')
        exit(1)
    else:
        print('Confirmed plugin data was correctly excluded')

    # Content-excludes checks - only run for '--check-x' flags that were actually passed
    check_category(
        data, 'email', ['common.emailmessage', 'common.emailthread'], args.check_email
    )
    check_category(data, 'tokens', ['users.apitoken'], args.check_tokens)
    check_category(
        data,
        'sso',
        ['socialaccount.socialapp', 'socialaccount.socialtoken'],
        args.check_sso,
    )
    check_category(
        data,
        'session',
        ['sessions.session', 'usersessions.usersession'],
        args.check_session,
    )
    check_permissions(data, args.check_permissions)

    print('All checks passed successfully!')
