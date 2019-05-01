""" This module provides template tags for extra functionality
over and above the built-in Django tags.
"""

from django import template

register = template.Library()


@register.simple_tag()
def multiply(x, y, *args, **kwargs):
    return x * y
