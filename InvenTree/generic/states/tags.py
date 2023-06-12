"""Provide templates for the various model status codes."""

from django.utils.safestring import mark_safe

from generic.templatetags.generic import register
from InvenTree.helpers import inheritors

from .states import StatusCode


@register.simple_tag
def status_label(typ: str, key: int, *args, **kwargs):
    """Render a status label."""
    state = {cls.tag(): cls for cls in inheritors(StatusCode)}.get(typ, None)
    if state:
        return mark_safe(state.render(key, large=kwargs.get('large', False)))
    raise ValueError(f"Unknown status type '{typ}'")
