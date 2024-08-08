"""Provide templates for the various model status codes."""

from django.utils.safestring import mark_safe

from generic.templatetags.generic import register

from .custom import get_custom_classes, get_custom_status_labels


@register.simple_tag
def status_label(typ: str, key: int, keys=None, *args, **kwargs):
    """Render a status label."""
    if keys is None:
        keys = {cls.tag(): cls for cls in get_custom_classes(include_custom=False)}
    state = keys.get(typ, None)

    if state:
        return mark_safe(state.render(key, large=kwargs.get('large', False)))
    raise ValueError(f"Unknown status type '{typ}'")


@register.simple_tag
def display_status_label(typ: str, key: int, fallback: int, *args, **kwargs):
    """Render a status label."""
    states = get_custom_status_labels()
    if key:
        render_key = int(key)
    else:
        render_key = fallback
    return status_label(typ, render_key, *args, keys=states, **kwargs)
