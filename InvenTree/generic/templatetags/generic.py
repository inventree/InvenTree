"""Template tags for generic *things*."""

from django import template

register = template.Library()
from generic.states.tags import status_label  # noqa: E402

__all__ = [status_label]
