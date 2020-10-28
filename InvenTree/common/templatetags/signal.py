import importlib

from django import template
from django.utils.safestring import mark_safe
from ..signals import nav_topbar

register = template.Library()



@register.simple_tag
def signal(signame: str, request, **kwargs):
    """
    Send a signal and return the concatenated return values of all responses.
    Usage::
        {% signal request "path.to.signal" argument="value" ... %}
    """
    sigstr = signame.rsplit('.', 1)
    sigmod = importlib.import_module(sigstr[0])
    signal = getattr(sigmod, sigstr[1])
    _html = []
    for receiver, response in signal.send(request, **kwargs):
        if response:
            _html.append(response)
    return mark_safe("".join(_html))

@register.simple_tag(takes_context=True)
def get_extension_navbar(context):
    tabs = sorted(
        sum((list(a[1]) for a in nav_topbar.send(context.request,
                                                 request=context.request)), []),
        key=lambda r: (1 if r.get('parent') else 0, r['label'])
    )
    return tabs
