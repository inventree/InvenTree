""" Version information for InvenTree.
Provides information on the current InvenTree version
"""

import subprocess

INVENTREE_SW_VERSION = "0.0.10"


def inventreeVersion():
    """ Returns the InvenTree version string """
    return INVENTREE_SW_VERSION


def inventreeCommitHash():
    """ Returns the git commit hash for the running codebase """

    return str(subprocess.check_output('git rev-parse --short HEAD'.split()), 'utf-8').strip()


def inventreeCommitDate():
    """ Returns the git commit date for the running codebase """

    d = str(subprocess.check_output('git show -s --format=%ci'.split()), 'utf-8').strip()

    return d.split(' ')[0]
