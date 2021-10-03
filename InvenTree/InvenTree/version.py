""" Version information for InvenTree.
Provides information on the current InvenTree version
"""

import subprocess
import django
import re

import common.models

INVENTREE_SW_VERSION = "0.5.1"

INVENTREE_API_VERSION = 12

"""
Increment this API version number whenever there is a significant change to the API that any clients need to know about

v12 -> 2021-09-07
    - Adds API endpoint to receive stock items against a PurchaseOrder

v11 -> 2021-08-26
    - Adds "units" field to PartBriefSerializer
    - This allows units to be introspected from the "part_detail" field in the StockItem serializer

v10 -> 2021-08-23
    - Adds "purchase_price_currency" to StockItem serializer
    - Adds "purchase_price_string" to StockItem serializer
    - Purchase price is now writable for StockItem serializer

v9  -> 2021-08-09
    - Adds "price_string" to part pricing serializers

v8  -> 2021-07-19
    - Refactors the API interface for SupplierPart and ManufacturerPart models
    - ManufacturerPart objects can no longer be created via the SupplierPart API endpoint

v7  -> 2021-07-03
    - Introduced the concept of "API forms" in https://github.com/inventree/InvenTree/pull/1716
    - API OPTIONS endpoints provide comprehensive field metedata
    - Multiple new API endpoints added for database models

v6  -> 2021-06-23
    - Part and Company images can now be directly uploaded via the REST API

v5  -> 2021-06-21
    - Adds API interface for manufacturer part parameters

v4  -> 2021-06-01
    - BOM items can now accept "variant stock" to be assigned against them
    - Many slight API tweaks were needed to get this to work properly!

v3  -> 2021-05-22:
    - The updated StockItem "history tracking" now uses a different interface

"""


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
    Release -> "major.minor"
    
    """

    if isInvenTreeDevelopmentVersion():
        return "latest"
    else:
        major, minor, patch = inventreeVersionTuple()

        return f"{major}.{minor}"


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
