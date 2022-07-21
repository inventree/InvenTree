"""
Version information for InvenTree.
Provides information on the current InvenTree version
"""

import re
import subprocess

import django

import common.models
from InvenTree.api_version import INVENTREE_API_VERSION

# InvenTree software version
INVENTREE_SW_VERSION = "0.7.6"


def inventreeInstanceName():
    """ Returns the InstanceName settings for the current database """
    return common.models.InvenTreeSetting.get_setting("INVENTREE_INSTANCE", "")


def inventreeInstanceTitle():
    """ Returns the InstanceTitle for the current database """
    if common.models.InvenTreeSetting.get_setting("INVENTREE_INSTANCE_TITLE", False):
        return common.models.InvenTreeSetting.get_setting("INVENTREE_INSTANCE", "")
    else:
        return 'InvenTree'


def inventreeVersion():
    """ Returns the InvenTree version string """
    return INVENTREE_SW_VERSION.lower().strip()


def inventreeVersionTuple(version=None):
    """ Return the InvenTree version string as (maj, min, sub) tuple """

    if version is None:
        version = INVENTREE_SW_VERSION

    match = re.match(r"^.*(\d+)\.(\d+)\.(\d+).*$", str(version))

    return [int(g) for g in match.groups()]


def isInvenTreeDevelopmentVersion():
    """
    Return True if current InvenTree version is a "development" version
    """
    return inventreeVersion().endswith('dev')


def inventreeDocsVersion():
    """
    Return the version string matching the latest documentation.

    Development -> "latest"
    Release -> "major.minor.sub" e.g. "0.5.2"

    """

    if isInvenTreeDevelopmentVersion():
        return "latest"
    else:
        return INVENTREE_SW_VERSION  # pragma: no cover


def isInvenTreeUpToDate():
    """
    Test if the InvenTree instance is "up to date" with the latest version.

    A background task periodically queries GitHub for latest version,
    and stores it to the database as INVENTREE_LATEST_VERSION
    """

    latest = common.models.InvenTreeSetting.get_setting('INVENTREE_LATEST_VERSION', backup_value=None, create=False)

    # No record for "latest" version - we must assume we are up to date!
    if not latest:
        return True

    # Extract "tuple" version (Python can directly compare version tuples)
    latest_version = inventreeVersionTuple(latest)  # pragma: no cover
    inventree_version = inventreeVersionTuple()  # pragma: no cover

    return inventree_version >= latest_version  # pragma: no cover


def inventreeApiVersion():
    return INVENTREE_API_VERSION


def inventreeDjangoVersion():
    """ Return the version of Django library """
    return django.get_version()


def inventreeCommitHash():
    """ Returns the git commit hash for the running codebase """

    try:
        return str(subprocess.check_output('git rev-parse --short HEAD'.split()), 'utf-8').strip()
    except:  # pragma: no cover
        return None


def inventreeCommitDate():
    """ Returns the git commit date for the running codebase """

    try:
        d = str(subprocess.check_output('git show -s --format=%ci'.split()), 'utf-8').strip()
        return d.split(' ')[0]
    except:  # pragma: no cover
        return None
