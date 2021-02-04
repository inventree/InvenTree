"""
Custom template tags for report generation
"""

import os

from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag()
def asset(filename):
    """
    Return fully-qualified path for an upload report asset file.
    """

    path = os.path.join(settings.MEDIA_ROOT, 'report', 'assets', filename)
    path = os.path.abspath(path)

    return f"file://{path}"
