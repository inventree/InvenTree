"""
Ensure that the release tag matches the InvenTree version number:

master / main branch:
    - version number must end with 'dev'

stable branch:
    - version number must *not* end with 'dev'
    - version number cannot already exist as a release tag

tagged branch:
    - version number must match tag being built
    - version number cannot already exist as a release tag

"""

import argparse
import os
import re
import sys

if __name__ == '__main__':

    here = os.path.abspath(os.path.dirname(__file__))

    # GITHUB_REF_TYPE may be either 'branch' or 'tag'
    GITHUB_REF_TYPE = os.environ['GITHUB_REF_TYPE']

    # GITHUB_REF may be either 'refs/heads/<branch>' or 'refs/heads/<tag>'
    GITHUB_REF = os.environ['GITHUB_REF']

    # GITHUB_BASE_REF is the base branch e.g. 'master' or 'stable'
    GITHUB_BASE_REF = os.environ['GITHUB_BASE_REF']

    version_file = os.path.join(here, '..', 'InvenTree', 'InvenTree', 'version.py')

    version = None

    print("GITHUB_REF_TYPE:", GITHUB_REF_TYPE)
    print("GITHUB_REF:", GITHUB_REF)
    print("GITHUB_BASE_REF:", GITHUB_BASE_REF)

    git_sha = os.environ['GITHUB_SHA']

    print("Git SHA:", git_sha)

    with open(version_file, 'r') as f:

        text = f.read()

        # Extract the InvenTree software version
        results = re.findall(r'INVENTREE_SW_VERSION = "(.*)"', text)

        if len(results) != 1:
            print(f"Could not find INVENTREE_SW_VERSION in {version_file}")
            sys.exit(1)

        version = results[0]

    print(f"InvenTree Version: '{version}'")

    if GITHUB_BASE_REF == 'stable' and GITHUB_REF_TYPE == 'branch':
        print("Checking requirements for 'stable' release")

        pattern = r"^\d+(\.\d+)+$"
        result = re.match(pattern, version)

        if result is None:
            print(f"Version number '{version}' does not match required pattern for stable branch")
            sys.exit(1)
        else:
            print(f"Version number '{version}' matches stable branch")

    elif GITHUB_BASE_REF in ['master', 'main'] and GITHUB_REF_TYPE == 'branch':
        print("Checking requirements for main development branch:")

        pattern = r"^\d+(\.\d+)+ dev$"
        result = re.match(pattern, version)

        if result is None:
            print(f"Version number '{version}' does not match required pattern for development branch")
            sys.exit(1)
        else:
            print(f"Version number '{version}' matches development branch")

    elif GITHUB_REF_TYPE == 'tag':
        print("Checking requirements for tagged release")

    else:
        print("Unsupported branch / version combination:")
        print(f"InvenTree Version: {version}")
        print("GITHUB_REF_TYPE:", GITHUB_REF_TYPE)
        print("GITHUB_REF:", GITHUB_REF)
        print("GITHUB_BASE_REF:", GITHUB_BASE_REF)
        sys.exit(1)

    sys.exit(0)

    # error out
    sys.exit(1)

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
