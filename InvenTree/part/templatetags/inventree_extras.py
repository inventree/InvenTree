""" This module provides template tags for extra functionality
over and above the built-in Django tags.
"""

from django import template
from InvenTree import version

register = template.Library()


@register.simple_tag()
def inrange(n, *args, **kwargs):
    """ Return range(n) for iterating through a numeric quantity """
    return range(n)
    

@register.simple_tag()
def multiply(x, y, *args, **kwargs):
    """ Multiply two numbers together """
    return x * y


@register.simple_tag()
def add(x, y, *args, **kwargs):
    """ Add two numbers together """
    return x + y
    

@register.simple_tag()
def part_allocation_count(build, part, *args, **kwargs):
    """ Return the total number of <part> allocated to <build> """

    return build.getAllocatedQuantity(part)


@register.simple_tag()
def inventree_version(*args, **kwargs):
    """ Return InvenTree version string """
    return version.inventreeVersion()


@register.simple_tag()
def inventree_commit(*args, **kwargs):
    """ Return InvenTree git commit hash string """
    return version.inventreeCommitHash()


@register.simple_tag()
def inventree_github_url(*args, **kwargs):
    """ Return URL for InvenTree github site """
    return "https://github.com/InvenTree"


@register.simple_tag()
def inventree_docs_url(*args, **kwargs):
    """ Return URL for InvenTree documenation site """
    return "https://inventree.github.io"
