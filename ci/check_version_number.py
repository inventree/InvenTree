"""
On release, ensure that the release tag matches the InvenTree version number!
"""

import argparse
import os
import re
import sys

if __name__ == '__main__':

    here = os.path.abspath(os.path.dirname(__file__))

    for var in [
        'GITHUB_EVENT_NAME',
        'GITHUB_REF',
        'GITHUB_REF_TYPE',
        'GITHUB_BASE_REF',
    ]:
        print(f"'{var}' - '{os.environ.get(var, '')}'")

    version_file = os.path.join(here, '..', 'InvenTree', 'InvenTree', 'version.py')

    version = None

    with open(version_file, 'r') as f:

        text = f.read()

        # Extract the InvenTree software version
        results = re.findall(r'INVENTREE_SW_VERSION = "(.*)"', text)

        if len(results) != 1:
            print(f"Could not find INVENTREE_SW_VERSION in {version_file}")
            sys.exit(1)

        version = results[0]

    print(f"InvenTree Version: '{version}'")

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='Compare against specified version tag', action='store')
    parser.add_argument('-r', '--release', help='Check that this is a release version', action='store_true')
    parser.add_argument('-d', '--dev', help='Check that this is a development version', action='store_true')
    parser.add_argument('-b', '--branch', help='Check against a particular branch', action='store')

    args = parser.parse_args()

    if args.branch:
        """
        Version number requirement depends on format of branch

        'master': development branch
        'stable': release branch
        """

        print(f"Checking version number for branch '{args.branch}'")

        if args.branch == 'master':
            print("- This is a development branch")
            args.dev = True
        elif args.branch == 'stable':
            print("- This is a stable release branch")
            args.release = True

    if args.dev:
        """
        Check that the current verrsion number matches the "development" format
        e.g. "0.5 dev"
        """

        print("Checking development branch")

        pattern = r"^\d+(\.\d+)+ dev$"

        result = re.match(pattern, version)

        if result is None:
            print(f"Version number '{version}' does not match required pattern for development branch")
            sys.exit(1)

    elif args.release:
        """
        Check that the current version number matches the "release" format
        e.g. "0.5.1"
        """

        print("Checking release branch")

        pattern = r"^\d+(\.\d+)+$"

        result = re.match(pattern, version)

        if result is None:
            print(f"Version number '{version}' does not match required pattern for stable branch")
            sys.exit(1)

    if args.tag:
        if args.tag != version:
            print(f"Release tag '{args.tag}' does not match INVENTREE_SW_VERSION '{version}'")
            sys.exit(1)

sys.exit(0)
