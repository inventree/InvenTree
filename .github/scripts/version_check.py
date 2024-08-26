"""Ensure that the release tag matches the InvenTree version number.

Behaviour:
master / main branch:
    - version number must end with 'dev'

tagged branch:
    - version number must match tag being built
    - version number cannot already exist as a release tag

"""

import itertools
import json
import os
import re
import sys
from pathlib import Path

import requests

REPO = os.getenv('GITHUB_REPOSITORY', 'inventree/inventree')
GITHUB_API_URL = os.getenv('GITHUB_API_URL', 'https://api.github.com')


def get_existing_release_tags(include_prerelease=True):
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
        match = re.match(r'^.*(\d+)\.(\d+)\.(\d+).*$', tag)

        if len(match.groups()) != 3:
            print(f"Version '{tag}' did not match expected pattern")
            continue

        if not include_prerelease and release['prerelease']:
            continue

        tags.append([int(x) for x in match.groups()])

    return tags


def check_version_number(version_string, allow_duplicate=False):
    """Check the provided version number.

    Returns True if the provided version is the 'newest' InvenTree release
    """
    print(f"Checking version '{version_string}'")

    # Check that the version string matches the required format
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?: dev)?$', version_string)

    if not match or len(match.groups()) != 3:
        raise ValueError(
            f"Version string '{version_string}' did not match required pattern"
        )

    version_tuple = [int(x) for x in match.groups()]

    # Look through the existing releases
    existing = get_existing_release_tags(include_prerelease=False)

    # Assume that this is the highest release, unless told otherwise
    highest_release = True

    for release in existing:
        if release == version_tuple and not allow_duplicate:
            raise ValueError(f"Duplicate release '{version_string}' exists!")

        if release > version_tuple:
            highest_release = False
            print(f'Found newer release: {release!s}')

    return highest_release


if __name__ == '__main__':
    # Ensure that we are running in GH Actions
    if os.environ.get('GITHUB_ACTIONS', '') != 'true':
        print('This script is intended to be run within a GitHub Action!')
        sys.exit(1)

    if 'only_version' in sys.argv:
        here = Path(__file__).parent.absolute()
        version_file = here.joinpath(
            '..', '..', 'src', 'backend', 'InvenTree', 'InvenTree', 'api_version.py'
        )
        text = version_file.read_text()
        results = re.findall(r"""INVENTREE_API_VERSION = (.*)""", text)
        # If 2. args is true lower the version number by 1
        if len(sys.argv) > 2 and sys.argv[2] == 'true':
            results[0] = str(int(results[0]) - 1)
        print(results[0])
        exit(0)

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

    here = Path(__file__).parent.absolute()
    version_file = here.joinpath(
        '..', '..', 'src', 'backend', 'InvenTree', 'InvenTree', 'version.py'
    )

    version = None

    with open(version_file, encoding='utf-8') as f:
        text = f.read()

        # Extract the InvenTree software version
        results = re.findall(r"""INVENTREE_SW_VERSION = '(.*)'""", text)

        if len(results) != 1:
            print(f'Could not find INVENTREE_SW_VERSION in {version_file}')
            sys.exit(1)

        version = results[0]

    print(f"InvenTree Version: '{version}'")

    # Check version number and look for existing versions
    # If a release is found which matches the current tag, throw an error

    allow_duplicate = False

    # Note: on a 'tag' (release) we *must* allow duplicate versions, as this *is* the version that has just been released
    if GITHUB_REF_TYPE == 'tag':
        allow_duplicate = True

    # Note: on a push to 'stable' branch we also allow duplicates
    if GITHUB_BASE_REF == 'stable':
        allow_duplicate = True

    highest_release = check_version_number(version, allow_duplicate=allow_duplicate)

    # Determine which docker tag we are going to use
    docker_tags = None

    if GITHUB_REF_TYPE == 'tag':
        # GITHUB_REF should be of the form /refs/heads/<tag>
        version_tag = GITHUB_REF.split('/')[-1]
        print(f"Checking requirements for tagged release - '{version_tag}':")

        if version_tag != version:
            print(f"Version number '{version}' does not match tag '{version_tag}'")
            sys.exit

        docker_tags = [version_tag, 'stable'] if highest_release else [version_tag]

    elif GITHUB_REF_TYPE == 'branch':
        # Otherwise we know we are targeting the 'master' branch
        docker_tags = ['latest']

    else:
        print('Unsupported branch / version combination:')
        print(f'InvenTree Version: {version}')
        print('GITHUB_REF_TYPE:', GITHUB_REF_TYPE)
        print('GITHUB_BASE_REF:', GITHUB_BASE_REF)
        print('GITHUB_REF:', GITHUB_REF)
        sys.exit(1)

    if docker_tags is None:
        print('Docker tags could not be determined')
        sys.exit(1)

    print(f"Version check passed for '{version}'!")
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
