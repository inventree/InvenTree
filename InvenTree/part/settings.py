"""
User-configurable settings for the Part app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from common.models import InvenTreeSetting


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
    Returns the defualt value fro the 'trackable' field for a Part object
    """

    return InvenTreeSetting.get_setting('PART_TRACKABLE')
