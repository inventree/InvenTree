"""Version information for InvenTree.

Provides information on the current InvenTree version
"""

import logging
import os
import pathlib
import platform
import re
import sys
from datetime import datetime as dt
from datetime import timedelta as td

from django.conf import settings

from .api_version import INVENTREE_API_TEXT, INVENTREE_API_VERSION

# InvenTree software version
INVENTREE_SW_VERSION = '1.3.0 dev'

# Minimum supported Python version
MIN_PYTHON_VERSION = (3, 11)

logger = logging.getLogger('inventree')

git_warning_txt = 'INVE-W3: Could not detect git information.'

# Discover git
try:
    from dulwich.errors import NotGitRepository
    from dulwich.porcelain import active_branch
    from dulwich.repo import Repo

    try:
        main_repo = Repo(pathlib.Path(__file__).parent.parent.parent.parent.parent)
        main_commit = main_repo[main_repo.head()]
    except NotGitRepository:
        output = logger.warning

        try:
            if settings.DOCKER:
                output = logger.info
        except Exception:
            # We may not have access to settings at this point
            pass

        output(git_warning_txt)

        main_repo = None
        main_commit = None

    try:
        main_branch = active_branch(main_repo) if main_repo else None
    except (KeyError, IndexError):
        logger.warning('INVE-W1: Current branch could not be detected.')
        main_branch = None
except ImportError:
    logger.warning(
        'INVE-W2: Dulwich module not found, git information will not be available.'
    )
    main_repo = None
    main_commit = None
    main_branch = None
except Exception as exc:
    logger.warning(git_warning_txt, exc_info=exc)
    main_repo = None
    main_commit = None
    main_branch = None


def checkMinPythonVersion():
    """Check that the Python version meets the minimum requirements."""
    V_MIN_MAJOR, V_MIN_MINOR = MIN_PYTHON_VERSION

    version = sys.version.split(' ')[0]
    docs = 'https://docs.inventree.org/en/stable/start/#python-requirements'

    msg = f"""
    INVE-E15: Python version not supported.
    InvenTree requires Python {V_MIN_MAJOR}.{V_MIN_MINOR} or above - you are running version {version}.
    - Refer to the InvenTree documentation for more information:
    - {docs}
    """

    if sys.version_info.major < V_MIN_MAJOR:
        raise RuntimeError(msg)

    if sys.version_info.major == V_MIN_MAJOR and sys.version_info.minor < V_MIN_MINOR:
        raise RuntimeError(msg)

    logger.info(f'Python version {version} - {sys.executable}')


def inventreeInstanceName() -> str:
    """Returns the InstanceName settings for the current database."""
    from common.settings import get_global_setting

    return get_global_setting('INVENTREE_INSTANCE')


def inventreeInstanceTitle() -> str:
    """Returns the InstanceTitle for the current database."""
    from common.settings import get_global_setting

    if get_global_setting('INVENTREE_INSTANCE_TITLE'):
        return get_global_setting('INVENTREE_INSTANCE')

    return 'InvenTree'


def inventreeVersion() -> str:
    """Returns the InvenTree version string."""
    return INVENTREE_SW_VERSION.lower().strip()


def inventreeVersionTuple(version=None):
    """Return the InvenTree version string as (maj, min, sub) tuple."""
    if version is None:
        version = INVENTREE_SW_VERSION

    match = re.match(r'^.*(\d+)\.(\d+)\.(\d+).*$', str(version))

    return [int(g) for g in match.groups()] if match else []


def isInvenTreeDevelopmentVersion() -> bool:
    """Return True if current InvenTree version is a "development" version."""
    return inventreeVersion().endswith('dev')


def inventreeDocsVersion() -> str:
    """Return the version string matching the latest documentation.

    Development -> "latest"
    Release -> "major.minor.sub" e.g. "0.5.2"
    """
    if isInvenTreeDevelopmentVersion():
        return 'latest'

    return INVENTREE_SW_VERSION


def inventreeDocUrl() -> str:
    """Return URL for InvenTree documentation site."""
    tag = inventreeDocsVersion()
    return f'https://docs.inventree.org/en/{tag}'


def inventreeAppUrl() -> str:
    """Return URL for InvenTree app site."""
    return 'https://docs.inventree.org/en/stable/app/'


def inventreeGithubUrl() -> str:
    """Return URL for InvenTree github site."""
    return 'https://github.com/InvenTree/InvenTree/'


def isInvenTreeUpToDate() -> bool:
    """Test if the InvenTree instance is "up to date" with the latest version.

    A background task periodically queries GitHub for latest version, and stores it to the database as "_INVENTREE_LATEST_VERSION"
    """
    from common.settings import get_global_setting

    latest = get_global_setting(
        '_INVENTREE_LATEST_VERSION', backup_value=None, create=False
    )

    # No record for "latest" version - we must assume we are up to date!
    if not latest:
        return True

    # Extract "tuple" version (Python can directly compare version tuples)
    latest_version = inventreeVersionTuple(latest)  # pragma: no cover
    inventree_version = inventreeVersionTuple()  # pragma: no cover

    return inventree_version >= latest_version  # pragma: no cover


def inventreeApiVersion() -> int:
    """Returns current API version of InvenTree."""
    return INVENTREE_API_VERSION


def parse_version_text():
    """Parse the version text to structured data."""
    patched_data = INVENTREE_API_TEXT.split('\n\n')
    # Remove first newline on latest version
    patched_data[0] = patched_data[0].replace('\n', '', 1)

    latest_version = f'v{INVENTREE_API_VERSION}'
    version_data = {}
    for version in patched_data:
        data = version.split('\n')

        version_split = data[0].split(' -> ')
        version_string = version_split[0].strip()
        if version_string == '':
            continue

        version_detail = (
            version_split[1].split(':', 1) if len(version_split) > 1 else ['']
        )
        new_data = {
            'version': version_string,
            'date': version_detail[0].strip(),
            'gh': version_detail[1].strip() if len(version_detail) > 1 else None,
            'text': data[1:],
            'latest': latest_version == version_string,
        }
        version_data[version_string] = new_data
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
        start_version = INVENTREE_API_VERSION - versions + 1

    return {
        f'v{a}': version_data.get(f'v{a}', None)
        for a in range(start_version, start_version + versions)
    }


def inventreeDjangoVersion():
    """Returns the version of Django library."""
    import django

    return django.get_version()


def inventreePythonVersion():
    """Returns the version of python."""
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


def inventreeBranch():
    """Returns the branch for the running codebase - if set."""
    # First look in the environment variables, e.g. if running in docker

    branch = os.environ.get('INVENTREE_PKG_BRANCH', '')

    if branch:
        return ' '.join(branch.splitlines())

    if main_branch is None:
        return None
    return main_branch.decode('utf-8')


def inventreeTarget():
    """Returns the target platform for the running codebase - if set."""
    # First look in the environment variables, e.g. if running in docker

    return os.environ.get('INVENTREE_PKG_TARGET', None)


def inventreePlatform():
    """Returns the platform for the instance."""
    return platform.platform(aliased=True)


def inventreeDatabase():
    """Return the InvenTree database backend e.g. 'postgresql'."""
    from django.conf import settings

    return settings.DB_ENGINE


def inventree_identifier(override_announce: bool = False):
    """Return the InvenTree instance ID."""
    from common.settings import get_global_setting

    if override_announce or get_global_setting(
        'INVENTREE_ANNOUNCE_ID', environment_key='INVENTREE_ANNOUNCE_ID'
    ):
        return get_global_setting('INVENTREE_INSTANCE_ID', default='')
    return None
