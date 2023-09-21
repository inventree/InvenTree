"""Sample plugin for versioning."""
from plugin import InvenTreePlugin


class VersionPlugin(InvenTreePlugin):
    """A small version sample."""

    NAME = "version"
    MAX_VERSION = '0.1.0'
