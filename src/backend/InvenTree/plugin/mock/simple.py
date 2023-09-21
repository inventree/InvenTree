"""Very simple sample plugin"""

from plugin import InvenTreePlugin


class SimplePlugin(InvenTreePlugin):
    """A very simple plugin."""

    NAME = 'SimplePlugin'
    SLUG = "simple"
