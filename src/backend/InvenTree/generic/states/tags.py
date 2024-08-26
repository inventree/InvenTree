"""Provide templates for the various model status codes."""

from django.utils.safestring import mark_safe

from generic.templatetags.generic import register

from .custom import get_custom_status_labels


@register.simple_tag
def status_label(typ: str, key: int, include_custom: bool = False, *args, **kwargs):
    """Render a status label."""
    state = get_custom_status_labels(include_custom=include_custom).get(typ, None)
    if state:
        return mark_safe(state.render(key, large=kwargs.get('large', False)))
    raise ValueError(f"Unknown status type '{typ}'")


@register.simple_tag
def display_status_label(typ: str, key: int, fallback: int, *args, **kwargs):
    """Render a status label."""
    render_key = int(key) if key else fallback
    return status_label(typ, render_key, *args, include_custom=True, **kwargs)
