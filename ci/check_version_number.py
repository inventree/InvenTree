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

    with open(version_file, 'r') as f:

        text = f.read()

        # Extract the InvenTree software version
        results = re.findall(r'INVENTREE_SW_VERSION = "(.*)"', text)

        if len(results) != 1:
            print(f"Could not find INVENTREE_SW_VERSION in {version_file}")
            sys.exit(1)

        version = results[0]

    print(f"InvenTree Version: '{version}'")

    # Determine which docker tag we are going to use
    docker_tag = None

    if GITHUB_BASE_REF == 'stable' and GITHUB_REF_TYPE == 'branch':
        print("Checking requirements for 'stable' release")

        pattern = r"^\d+(\.\d+)+$"
        result = re.match(pattern, version)

        if result is None:
            print(f"Version number '{version}' does not match required pattern for stable branch")
            sys.exit(1)
        else:
            print(f"Version number '{version}' matches stable branch")

        docker_tag = 'stable'

    elif GITHUB_BASE_REF in ['master', 'main'] and GITHUB_REF_TYPE == 'branch':
        print("Checking requirements for main development branch:")

        pattern = r"^\d+(\.\d+)+ dev$"
        result = re.match(pattern, version)

        if result is None:
            print(f"Version number '{version}' does not match required pattern for development branch")
            sys.exit(1)
        else:
            print(f"Version number '{version}' matches development branch")

        docker_tag = 'latest'

    elif GITHUB_REF_TYPE == 'tag':
        # GITHUB_REF should be of th eform /refs/heads/<tag>
        version_tag = GITHUB_REF.split('/')[-1]
        print(f"Checking requirements for tagged release - '{version_tag}'")

        if version_tag != version:
            print(f"Version number '{version}' does not match tag '{version_tag}'")
            sys.exit

        # TODO: Check if there is already a release with this tag!

        docker_tag = version_tag

    else:
        print("Unsupported branch / version combination:")
        print(f"InvenTree Version: {version}")
        print("GITHUB_REF_TYPE:", GITHUB_REF_TYPE)
        print("GITHUB_REF:", GITHUB_REF)
        print("GITHUB_BASE_REF:", GITHUB_BASE_REF)
        sys.exit(1)

    if docker_tag is None:
        print("Docker tag could not be determined")
        sys.exit(1)

    print(f"Version check passed for '{version}'!")
    print(f"Docker tag: '{docker_tag}'")

    # Ref: https://getridbug.com/python/how-to-set-environment-variables-in-github-actions-using-python/
    with open(os.getenv('GITHUB_ENV'), 'a') as env_file:
        env_file.write(f"docker_tag={docker_tag}")
