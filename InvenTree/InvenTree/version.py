""" Version information for InvenTree.
Provides information on the current InvenTree version
"""

import subprocess

INVENTREE_SW_VERSION = "0.0.3"


def inventreeVersion():
    """ Returns the InvenTree version string """
    return INVENTREE_SW_VERSION


def inventreeCommitHash():
    """ Returns the git commit hash for the running codebase """

    # TODO - This doesn't seem to work when running under gunicorn. Why is this?!
    commit = str(subprocess.check_output('git rev-parse --short HEAD'.split()), 'utf-8').strip()

    return commit
