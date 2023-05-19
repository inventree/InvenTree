"""Provide templates for the various model status codes."""

from django import template
from django.utils.safestring import mark_safe

from generic.states.states import StatusCode
from InvenTree.helpers import inheritors_attr

register = template.Library()


@register.simple_tag
def status_label(typ: str, key: int, *args, **kwargs):
    """Render a status label."""
    state = inheritors_attr(StatusCode, '_TAG').get(typ, None)
    if state:
        return mark_safe(state.render(key, large=kwargs.get('large', False)))
    raise ValueError(f"Unknown status type '{typ}'")
