"""Version information for InvenTree.

Provides information on the current InvenTree version
"""

import os
import pathlib
import platform
import re
from datetime import datetime as dt
from datetime import timedelta as td

import django
from django.conf import settings

from dulwich.repo import NotGitRepository, Repo

from .api_version import INVENTREE_API_VERSION

# InvenTree software version
INVENTREE_SW_VERSION = "0.13.0 dev"

# Discover git
try:
    main_repo = Repo(pathlib.Path(__file__).parent.parent.parent)
    main_commit = main_repo[main_repo.head()]
except (NotGitRepository, FileNotFoundError):
    main_commit = None


def inventreeInstanceName():
    """Returns the InstanceName settings for the current database."""
    import common.models

    return common.models.InvenTreeSetting.get_setting("INVENTREE_INSTANCE", "")


def inventreeInstanceTitle():
    """Returns the InstanceTitle for the current database."""
    import common.models

    if common.models.InvenTreeSetting.get_setting("INVENTREE_INSTANCE_TITLE", False):
        return common.models.InvenTreeSetting.get_setting("INVENTREE_INSTANCE", "")
    else:
        return 'InvenTree'


def inventreeVersion():
    """Returns the InvenTree version string."""
    return INVENTREE_SW_VERSION.lower().strip()


def inventreeVersionTuple(version=None):
    """Return the InvenTree version string as (maj, min, sub) tuple."""
    if version is None:
        version = INVENTREE_SW_VERSION

    match = re.match(r"^.*(\d+)\.(\d+)\.(\d+).*$", str(version))

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
        return "latest"
    else:
        return INVENTREE_SW_VERSION  # pragma: no cover


def isInvenTreeUpToDate():
    """Test if the InvenTree instance is "up to date" with the latest version.

    A background task periodically queries GitHub for latest version, and stores it to the database as "_INVENTREE_LATEST_VERSION"
    """
    import common.models
    latest = common.models.InvenTreeSetting.get_setting('_INVENTREE_LATEST_VERSION', backup_value=None, create=False)

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


def inventreeDjangoVersion():
    """Returns the version of Django library."""
    return django.get_version()


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

    commit_dt = dt.fromtimestamp(main_commit.commit_time) + td(seconds=main_commit.commit_timezone)
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
