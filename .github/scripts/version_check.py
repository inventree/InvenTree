"""Ensure that the release tag matches the InvenTree version number.

Behaviour:
master / main branch:
    - version number must end with 'dev'

tagged branch:
    - version number must match tag being built
    - version number cannot already exist as a release tag

"""

import argparse
import itertools
import json
import os
import re
import sys
from pathlib import Path

import requests

REPO = os.getenv('GITHUB_REPOSITORY', 'inventree/inventree')
GITHUB_API_URL = os.getenv('GITHUB_API_URL', 'https://api.github.com')


def get_src_dir() -> Path:
    """Return the path to the InvenTree source directory."""
    here = Path(__file__).parent.absolute()
    src_dir = here.joinpath('..', '..', 'src', 'backend', 'InvenTree', 'InvenTree')

    if not src_dir.exists():
        raise FileNotFoundError(
            f"Could not find InvenTree source directory: '{src_dir}'"
        )

    return src_dir


def get_inventree_version() -> str:
    """Return the InvenTree version string."""
    src_dir = get_src_dir()
    version_file = src_dir.joinpath('version.py')

    if not version_file.exists():
        raise FileNotFoundError(
            f"Could not find InvenTree version file: '{version_file}'"
        )

    with open(version_file, encoding='utf-8') as f:
        text = f.read()

        # Extract the InvenTree software version
        results = re.findall(r"""INVENTREE_SW_VERSION = '(.*)'""", text)

        if len(results) != 1:
            raise ValueError(f'Could not find INVENTREE_SW_VERSION in {version_file}')

        return results[0]


def get_api_version() -> str:
    """Return the InvenTree API version string."""
    src_dir = get_src_dir()
    api_version_file = src_dir.joinpath('api_version.py')

    if not api_version_file.exists():
        raise FileNotFoundError(
            f"Could not find InvenTree API version file: '{api_version_file}'"
        )

    with open(api_version_file, encoding='utf-8') as f:
        text = f.read()

        # Extract the InvenTree software version
        results = re.findall(r"""INVENTREE_API_VERSION = (.*)""", text)

        if len(results) != 1:
            raise ValueError(
                f'Could not find INVENTREE_API_VERSION in {api_version_file}'
            )

        return results[0].strip().strip('"').strip("'")


def version_number_to_tuple(version_string: str) -> tuple[int, int, int, str]:
    """Validate a version number string, and convert to a tuple of integers.

    e.g. 1.1.0
    e.g. 1.1.0 dev
    e.g. 1.2.3-rc2
    """
    pattern = r'^(\d+)\.(\d+)\.(\d+)[\s-]?(.*)?$'

    match = re.match(pattern, version_string)

    if not match or len(match.groups()) < 3:
        raise ValueError(
            f"Version string '{version_string}' did not match required pattern"
        )

    result = tuple(int(x) for x in match.groups()[:3])

    # Add optional prerelease tag
    if len(match.groups()) > 3:
        result += (match.groups()[3] or '',)
    else:
        result += ('',)

    return result


def get_existing_release_tags(include_prerelease: bool = True):
    """Request information on existing releases via the GitHub API."""
    # Check for github token
    token = os.getenv('GITHUB_TOKEN', None)
    headers = None

    if token:
        headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(f'{GITHUB_API_URL}/repos/{REPO}/releases', headers=headers)

    if response.status_code != 200:
        raise ValueError(
            f'Unexpected status code from GitHub API: {response.status_code}'
        )

    data = json.loads(response.text)

    # Return a list of all tags
    tags = []

    for release in data:
        tag = release['tag_name'].strip()

        version_tuple = version_number_to_tuple(tag)

        if len(version_tuple) >= 4 and version_tuple[3]:
            # Skip prerelease tags
            if not include_prerelease:
                print('-- skipping prerelease tag:', tag)
                continue

        tags.append(tag)

    return tags


def check_version_number(version_string, allow_duplicate=False):
    """Check the provided version number.

    Returns True if the provided version is the 'newest' InvenTree release
    """
    print(f"Checking version '{version_string}'")

    version_tuple = version_number_to_tuple(version_string)

    # Look through the existing releases
    existing = get_existing_release_tags(include_prerelease=False)

    # Assume that this is the highest release, unless told otherwise
    highest_release = True

    # A non-standard tag cannot be the 'highest' release
    if len(version_tuple) >= 4 and version_tuple[3]:
        highest_release = False
        print(f"-- Version tag '{version_string}' cannot be the highest release")

    for release in existing:
        if version_string == release and not allow_duplicate:
            raise ValueError(f"Duplicate release '{version_string}' exists!")

        release_tuple = version_number_to_tuple(release)

        if release_tuple > version_tuple:
            highest_release = False
            print(f'Found newer release: {release!s}')

    return highest_release


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='InvenTree Version Check')
    parser.add_argument(
        '--show-version',
        action='store_true',
        help='Print the InvenTree version and exit',
    )
    parser.add_argument(
        '--show-api-version',
        action='store_true',
        help='Print the InvenTree API version and exit',
    )
    parser.add_argument(
        '--decrement-api',
        type=str,
        default='false',
        help='Decrement the API version by 1 and print',
    )

    args = parser.parse_args()

    inventree_version = get_inventree_version()
    inventree_api_version = int(get_api_version())

    if args.show_version:
        print(inventree_version)
        sys.exit(0)

    if args.show_api_version:
        if args.decrement_api.lower() == 'true':
            inventree_api_version -= 1
        print(inventree_api_version)
        sys.exit(0)

    # Ensure that we are running in GH Actions
    if os.environ.get('GITHUB_ACTIONS', '') != 'true':
        print('This script is intended to be run within a GitHub Action!')
        sys.exit(1)

    # GITHUB_REF_TYPE may be either 'branch' or 'tag'
    GITHUB_REF_TYPE = os.environ['GITHUB_REF_TYPE']

    # GITHUB_REF may be either 'refs/heads/<branch>' or 'refs/heads/<tag>'
    GITHUB_REF = os.environ['GITHUB_REF']
    GITHUB_REF_NAME = os.environ['GITHUB_REF_NAME']
    GITHUB_BASE_REF = os.environ['GITHUB_BASE_REF']

    # Print out version information, makes debugging actions *much* easier!
    print(f'GITHUB_REF: {GITHUB_REF}')
    print(f'GITHUB_REF_NAME: {GITHUB_REF_NAME}')
    print(f'GITHUB_REF_TYPE: {GITHUB_REF_TYPE}')
    print(f'GITHUB_BASE_REF: {GITHUB_BASE_REF}')

    print(f"InvenTree Version: '{inventree_version}'")

    # Check version number and look for existing versions
    # If a release is found which matches the current tag, throw an error

    allow_duplicate = False

    # Note: on a 'tag' (release) we *must* allow duplicate versions, as this *is* the version that has just been released
    if GITHUB_REF_TYPE == 'tag':
        allow_duplicate = True

    # Note: on a push to 'stable' branch we also allow duplicates
    if GITHUB_BASE_REF == 'stable':
        allow_duplicate = True

    highest_release = check_version_number(
        inventree_version, allow_duplicate=allow_duplicate
    )

    # Determine which docker tag we are going to use
    docker_tags = None

    if GITHUB_REF_TYPE == 'tag':
        # GITHUB_REF should be of the form /refs/heads/<tag>
        version_tag = GITHUB_REF.split('/')[-1]
        print(f"Checking requirements for tagged release - '{version_tag}':")

        if version_tag != inventree_version:
            print(
                f"Version number '{inventree_version}' does not match tag '{version_tag}'"
            )
            sys.exit

        docker_tags = [version_tag, 'stable'] if highest_release else [version_tag]

    elif GITHUB_REF_TYPE == 'branch':
        # Otherwise we know we are targeting the 'master' branch
        docker_tags = ['latest']

    else:
        print('Unsupported branch / version combination:')
        print(f'InvenTree Version: {inventree_version}')
        print('GITHUB_REF_TYPE:', GITHUB_REF_TYPE)
        print('GITHUB_BASE_REF:', GITHUB_BASE_REF)
        print('GITHUB_REF:', GITHUB_REF)
        sys.exit(1)

    if docker_tags is None:
        print('Docker tags could not be determined')
        sys.exit(1)

    print(f"Version check passed for '{inventree_version}'!")
    print(f"Docker tags: '{docker_tags}'")

    target_repos = [REPO.lower(), f'ghcr.io/{REPO.lower()}']

    # Ref: https://getridbug.com/python/how-to-set-environment-variables-in-github-actions-using-python/
    with open(os.getenv('GITHUB_ENV'), 'a', encoding='utf-8') as env_file:
        # Construct tag string
        tag_list = [[f'{r}:{t}' for t in docker_tags] for r in target_repos]
        tags = ','.join(itertools.chain(*tag_list))

        env_file.write(f'docker_tags={tags}\n')

        if GITHUB_REF_TYPE == 'tag' and highest_release:
            env_file.write('stable_release=true\n')
