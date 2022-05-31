"""
Ensure that the release tag matches the InvenTree version number:

master / main branch:
    - version number must end with 'dev'

tagged branch:
    - version number must match tag being built
    - version number cannot already exist as a release tag

"""

import json
import os
import re
import sys

import requests


def get_existing_release_tags():
    """Request information on existing releases via the GitHub API"""

    response = requests.get('https://api.github.com/repos/inventree/inventree/releases')

    if response.status_code != 200:
        raise ValueError(f'Unexpected status code from GitHub API: {response.status_code}')

    data = json.loads(response.text)

    # Return a list of all tags
    tags = []

    for release in data:
        tag = release['tag_name'].strip()
        match = re.match(r"^.*(\d+)\.(\d+)\.(\d+).*$", tag)

        if len(match.groups()) != 3:
            print(f"Version '{tag}' did not match expected pattern")
            continue

        tags.append([int(x) for x in match.groups()])

    return tags


def check_version_number(version_string):
    """Check the provided version number.

    Returns True if the provided version is the 'newest' InvenTree release
    """

    print(f"Checking version '{version_string}'")

    # Check that the version string matches the required format
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?: dev)?$", version_string)

    if not match or len(match.groups()) != 3:
        raise ValueError(f"Version string '{version_string}' did not match required pattern")

    version_tuple = [int(x) for x in match.groups()]

    # Look through the existing releases
    existing = get_existing_release_tags()

    # Assume that this is the highest release, unless told otherwise
    highest_release = True

    for release in existing:
        if release == version_tuple:
            raise ValueError(f"Duplicate release '{version_string}' exists!")

        if release > version_tuple:
            highest_release = False
            print(f"Found newer release: {str(release)}")

    return highest_release


if __name__ == '__main__':

    here = os.path.abspath(os.path.dirname(__file__))

    # GITHUB_REF_TYPE may be either 'branch' or 'tag'
    GITHUB_REF_TYPE = os.environ['GITHUB_REF_TYPE']

    # GITHUB_REF may be either 'refs/heads/<branch>' or 'refs/heads/<tag>'
    GITHUB_REF = os.environ['GITHUB_REF']

    GITHUB_BASE_REF = os.environ['GITHUB_BASE_REF']

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

    highest_release = check_version_number(version)

    # Determine which docker tag we are going to use
    docker_tags = None

    if GITHUB_REF_TYPE == 'tag':
        # GITHUB_REF should be of th eform /refs/heads/<tag>
        version_tag = GITHUB_REF.split('/')[-1]
        print(f"Checking requirements for tagged release - '{version_tag}':")

        if version_tag != version:
            print(f"Version number '{version}' does not match tag '{version_tag}'")
            sys.exit

        # TODO: Check if there is already a release with this tag!

        if highest_release:
            docker_tags = [version_tag, 'stable']
        else:
            docker_tags = [version_tag]

    elif GITHUB_REF_TYPE == 'branch':
        # Otherwise we know we are targetting the 'master' branch
        print("Checking requirements for 'master' development branch:")

        pattern = r"^\d+(\.\d+)+ dev$"
        result = re.match(pattern, version)

        if result is None:
            print(f"Version number '{version}' does not match required pattern for development branch")
            sys.exit(1)
        else:
            print(f"Version number '{version}' matches development branch")

        docker_tags = ['latest']

    else:
        print("Unsupported branch / version combination:")
        print(f"InvenTree Version: {version}")
        print("GITHUB_REF_TYPE:", GITHUB_REF_TYPE)
        print("GITHUB_BASE_REF:", GITHUB_BASE_REF)
        print("GITHUB_REF:", GITHUB_REF)
        sys.exit(1)

    if docker_tags is None:
        print("Docker tag could not be determined")
        sys.exit(1)

    print(f"Version check passed for '{version}'!")
    print(f"Docker tags: '{docker_tags}'")

    # Ref: https://getridbug.com/python/how-to-set-environment-variables-in-github-actions-using-python/
    with open(os.getenv('GITHUB_ENV'), 'a') as env_file:

        # Construct tag string
        tags = ",".join([f"inventree/inventree:{tag}" for tag in docker_tags])

        env_file.write(f"docker_tags={tags}\n")

        if GITHUB_REF_TYPE == 'tag' and highest_release:
            env_file.write("stable_release=true\n")
