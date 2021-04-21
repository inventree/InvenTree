""" Version information for InvenTree.
Provides information on the current InvenTree version
"""

import subprocess
import django
import re

import common.models

INVENTREE_SW_VERSION = "0.2.2 pre"

# Increment this number whenever there is a significant change to the API that any clients need to know about
INVENTREE_API_VERSION = 2


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
    return INVENTREE_SW_VERSION


def inventreeVersionTuple(version=None):
    """ Return the InvenTree version string as (maj, min, sub) tuple """

    if version is None:
        version = INVENTREE_SW_VERSION

    match = re.match(r"^.*(\d+)\.(\d+)\.(\d+).*$", str(version))

    return [int(g) for g in match.groups()]


def isInvenTreeUpToDate():
    """
    Test if the InvenTree instance is "up to date" with the latest version.

    A background task periodically queries GitHub for latest version,
    and stores it to the database as INVENTREE_LATEST_VERSION
    """

    latest = common.models.InvenTreeSetting.get_setting('INVENTREE_LATEST_VERSION', None)

    # No record for "latest" version - we must assume we are up to date!
    if not latest:
        return True

    # Extract "tuple" version (Python can directly compare version tuples)
    latest_version = inventreeVersionTuple(latest)
    inventree_version = inventreeVersionTuple()

    return inventree_version >= latest_version


def inventreeApiVersion():
    return INVENTREE_API_VERSION


def inventreeDjangoVersion():
    """ Return the version of Django library """
    return django.get_version()


def inventreeCommitHash():
    """ Returns the git commit hash for the running codebase """

    try:
        return str(subprocess.check_output('git rev-parse --short HEAD'.split()), 'utf-8').strip()
    except:
        return None


def inventreeCommitDate():
    """ Returns the git commit date for the running codebase """

    try:
        d = str(subprocess.check_output('git show -s --format=%ci'.split()), 'utf-8').strip()
        return d.split(' ')[0]
    except:
        return None
