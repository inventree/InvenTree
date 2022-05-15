"""
User-configurable settings for the Part app
"""

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
