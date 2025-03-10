"""Template tags for generic *things*."""

from django import template

register = template.Library()
from generic.states.tags import status_label

__all__ = ['status_label']
