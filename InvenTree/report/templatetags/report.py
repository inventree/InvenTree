"""
Custom template tags for report generation
"""

import os

from django import template
from django.conf import settings

from part.models import Part
from stock.models import StockItem

register = template.Library()


@register.simple_tag()
def asset(filename):
    """
    Return fully-qualified path for an upload report asset file.
    """

    path = os.path.join(settings.MEDIA_ROOT, 'report', 'assets', filename)
    path = os.path.abspath(path)

    return f"file://{path}"


@register.simple_tag()
def part_image(part):
    """
    Return a fully-qualified path for a part image
    """

    if type(part) is Part:
        img = part.image.name

    elif type(part) is StockItem:
        img = part.part.image.name

    else:
        img = ''

    path = os.path.join(settings.MEDIA_ROOT, img)
    path = os.path.abspath(path)

    if not os.path.exists(path) or not os.path.isfile(path):
        # Image does not exist
        # Return the 'blank' image
        path = os.path.join(settings.STATIC_ROOT, 'img', 'blank_image.png')
        path = os.path.abspath(path)

    return f"file://{path}"
