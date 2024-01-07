"""Version information for InvenTree.

Provides information on the current InvenTree version
"""

import os
import pathlib
import platform
import re
import sys
from datetime import datetime as dt
from datetime import timedelta as td

import django
from django.conf import settings

from dulwich.repo import NotGitRepository, Repo

from .api_version import INVENTREE_API_TEXT, INVENTREE_API_VERSION

# InvenTree software version
INVENTREE_SW_VERSION = '0.14.0 dev'

# Discover git
try:
    main_repo = Repo(pathlib.Path(__file__).parent.parent.parent)
    main_commit = main_repo[main_repo.head()]
except (NotGitRepository, FileNotFoundError):
    main_commit = None


def checkMinPythonVersion():
    """Check that the Python version is at least 3.9"""

    version = sys.version.split(' ')[0]
    docs = 'https://docs.inventree.org/en/stable/start/intro/#python-requirements'

    msg = f"""
    InvenTree requires Python 3.9 or above - you are running version {version}.
    - Refer to the InvenTree documentation for more information:
    - {docs}
    """

    if sys.version_info.major < 3:
        raise RuntimeError(msg)

    if sys.version_info.major == 3 and sys.version_info.minor < 9:
        raise RuntimeError(msg)

    print(f'Python version {version} - {sys.executable}')


def inventreeInstanceName():
    """Returns the InstanceName settings for the current database."""
    import common.models

    return common.models.InvenTreeSetting.get_setting('INVENTREE_INSTANCE', '')


def inventreeInstanceTitle():
    """Returns the InstanceTitle for the current database."""
    import common.models

    if common.models.InvenTreeSetting.get_setting('INVENTREE_INSTANCE_TITLE', False):
        return common.models.InvenTreeSetting.get_setting('INVENTREE_INSTANCE', '')
    return 'InvenTree'


def inventreeVersion():
    """Returns the InvenTree version string."""
    return INVENTREE_SW_VERSION.lower().strip()


def inventreeVersionTuple(version=None):
    """Return the InvenTree version string as (maj, min, sub) tuple."""
    if version is None:
        version = INVENTREE_SW_VERSION

    match = re.match(r'^.*(\d+)\.(\d+)\.(\d+).*$', str(version))

    return [int(g) for g in match.groups()]


def isInvenTreeDevelopmentVersion():
    """Return True if current InvenTree version is a "development" version."""
    return inventreeVersion().endswith('dev')


def inventreeDocsVersion():
    """Return the version string matching the latest documentation.

    Development -> "latest"
    Release -> "major.minor.sub" e.g. "0.5.2"
    """
    if isInvenTreeDevelopmentVersion():
        return 'latest'
    return INVENTREE_SW_VERSION  # pragma: no cover


def inventreeDocUrl():
    """Return URL for InvenTree documentation site."""
    tag = inventreeDocsVersion()
    return f'https://docs.inventree.org/en/{tag}'


def inventreeAppUrl():
    """Return URL for InvenTree app site."""
    return (f'{inventreeDocUrl()}/app/app',)


def inventreeCreditsUrl():
    """Return URL for InvenTree credits site."""
    return 'https://docs.inventree.org/en/latest/credits/'


def inventreeGithubUrl():
    """Return URL for InvenTree github site."""
    return 'https://github.com/InvenTree/InvenTree/'


def isInvenTreeUpToDate():
    """Test if the InvenTree instance is "up to date" with the latest version.

    A background task periodically queries GitHub for latest version, and stores it to the database as "_INVENTREE_LATEST_VERSION"
    """
    import common.models

    latest = common.models.InvenTreeSetting.get_setting(
        '_INVENTREE_LATEST_VERSION', backup_value=None, create=False
    )

    # No record for "latest" version - we must assume we are up to date!
    if not latest:
        return True

    # Extract "tuple" version (Python can directly compare version tuples)
    latest_version = inventreeVersionTuple(latest)  # pragma: no cover
    inventree_version = inventreeVersionTuple()  # pragma: no cover

    return inventree_version >= latest_version  # pragma: no cover


def inventreeApiVersion():
    """Returns current API version of InvenTree."""
    return INVENTREE_API_VERSION


def parse_version_text():
    """Parse the version text to structured data."""
    patched_data = INVENTREE_API_TEXT.split('\n\n')
    # Remove first newline on latest version
    patched_data[0] = patched_data[0].replace('\n', '', 1)

    version_data = {}
    for version in patched_data:
        data = version.split('\n')

        version_split = data[0].split(' -> ')
        version_detail = (
            version_split[1].split(':', 1) if len(version_split) > 1 else ['']
        )
        new_data = {
            'version': version_split[0].strip(),
            'date': version_detail[0].strip(),
            'gh': version_detail[1].strip() if len(version_detail) > 1 else None,
            'text': data[1:],
            'latest': False,
        }
        version_data[new_data['version']] = new_data
    return version_data


INVENTREE_API_TEXT_DATA = parse_version_text()
"""Pre-processed API version text."""


def inventreeApiText(versions: int = 10, start_version: int = 0):
    """Returns API version descriptors.

    Args:
        versions: Number of versions to return. Default: 10
        start_version: first version to report. Defaults to return the latest {versions} versions.
    """
    version_data = INVENTREE_API_TEXT_DATA

    # Define the range of versions to return
    if start_version == 0:
        start_version = INVENTREE_API_VERSION - versions

    return {
        f'v{a}': version_data.get(f'v{a}', None)
        for a in range(start_version, start_version + versions)
    }


def inventreeDjangoVersion():
    """Returns the version of Django library."""
    return django.get_version()


def inventreePythonVersion():
    """Returns the version of python"""
    return sys.version.split(' ')[0]


def inventreeCommitHash():
    """Returns the git commit hash for the running codebase."""
    # First look in the environment variables, i.e. if running in docker
    commit_hash = os.environ.get('INVENTREE_COMMIT_HASH', '')

    if commit_hash:
        return commit_hash

    if main_commit is None:
        return None
    return main_commit.sha().hexdigest()[0:7]


def inventreeCommitDate():
    """Returns the git commit date for the running codebase."""
    # First look in the environment variables, e.g. if running in docker
    commit_date = os.environ.get('INVENTREE_COMMIT_DATE', '')

    if commit_date:
        return commit_date.split(' ')[0]

    if main_commit is None:
        return None

    commit_dt = dt.fromtimestamp(main_commit.commit_time) + td(
        seconds=main_commit.commit_timezone
    )
    return str(commit_dt.date())


def inventreeInstaller():
    """Returns the installer for the running codebase - if set."""
    # First look in the environment variables, e.g. if running in docker

    installer = os.environ.get('INVENTREE_PKG_INSTALLER', '')

    if installer:
        return installer
    elif settings.DOCKER:
        return 'DOC'
    elif main_commit is not None:
        return 'GIT'

    return None


def inventreeBranch():
    """Returns the branch for the running codebase - if set."""
    # First look in the environment variables, e.g. if running in docker

    branch = os.environ.get('INVENTREE_PKG_BRANCH', '')

    if branch:
        return branch

    if main_commit is None:
        return None

    try:
        branch = main_repo.refs.follow(b'HEAD')[0][1].decode()
        return branch.removeprefix('refs/heads/')
    except IndexError:
        return None  # pragma: no cover


def inventreeTarget():
    """Returns the target platform for the running codebase - if set."""
    # First look in the environment variables, e.g. if running in docker

    return os.environ.get('INVENTREE_PKG_TARGET', None)


def inventreePlatform():
    """Returns the platform for the instance."""
    return platform.platform(aliased=True)


def inventreeDatabase():
    """Return the InvenTree database backend e.g. 'postgresql'."""
    db = settings.DATABASES['default']
    return db.get('ENGINE', None).replace('django.db.backends.', '')
