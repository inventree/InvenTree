"""
User-configurable settings for the Part app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from common.models import InvenTreeSetting


def part_assembly_default():
    """
    Returns the default value for the 'assembly' field of a Part object
    """

    return InvenTreeSetting.get_setting('PART_ASSEMBLY')


def part_template_default():
    """
    Returns the default value for the 'is_template' field of a Part object
    """

    return InvenTreeSetting.get_setting('PART_TEMPLATE')


def part_virtual_default():
    """
    Returns the default value for the 'is_virtual' field of Part object
    """

    return InvenTreeSetting.get_setting('PART_VIRTUAL')


def part_component_default():
    """
    Returns the default value for the 'component' field of a Part object
    """

    return InvenTreeSetting.get_setting('PART_COMPONENT')


def part_purchaseable_default():
    """
    Returns the default value for the 'purchasable' field for a Part object
    """

    return InvenTreeSetting.get_setting('PART_PURCHASEABLE')


def part_salable_default():
    """
    Returns the default value for the 'salable' field for a Part object
    """

    return InvenTreeSetting.get_setting('PART_SALABLE')


def part_trackable_default():
    """
    Returns the default value for the 'trackable' field for a Part object
    """

    return InvenTreeSetting.get_setting('PART_TRACKABLE')


# CONSTANTS

# Every brace pair is a field parser within which a field name of part has to be defined in the format part.$field_name
# When full name is constructed, It would be replaced by its value from the database and if the value is None,
# the entire field_parser i.e {.*} would be replaced with ''.
# Other characters inside and between the brace pairs would be copied as is.
PART_NAME_FORMAT = '{part.IPN | }{part.name}{ | part.revision}'

