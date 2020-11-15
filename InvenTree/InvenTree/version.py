""" Version information for InvenTree.
Provides information on the current InvenTree version
"""

import subprocess
import django

import common.models

INVENTREE_SW_VERSION = "0.1.5 pre"


def inventreeInstanceName():
    """ Returns the InstanceName settings for the current database """
    return common.models.InvenTreeSetting.get_setting("INVENTREE_INSTANCE", "")


def inventreeVersion():
    """ Returns the InvenTree version string """
    return INVENTREE_SW_VERSION


def inventreeDjangoVersion():
    """ Return the version of Django library """
    return django.get_version()


def inventreeCommitHash():
    """ Returns the git commit hash for the running codebase """

    try:
        return str(subprocess.check_output('git rev-parse --short HEAD'.split()), 'utf-8').strip()
    except FileNotFoundError:
        return None


def inventreeCommitDate():
    """ Returns the git commit date for the running codebase """

    try:
        d = str(subprocess.check_output('git show -s --format=%ci'.split()), 'utf-8').strip()
        return d.split(' ')[0]
    except FileNotFoundError:
        return None
