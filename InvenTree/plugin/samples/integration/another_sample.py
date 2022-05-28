"""Sample implementation for IntegrationPlugin"""
from plugin import InvenTreePlugin
from plugin.mixins import UrlsMixin


class NoIntegrationPlugin(InvenTreePlugin):
    """A basic plugin"""

    NAME = "NoIntegrationPlugin"


class WrongIntegrationPlugin(UrlsMixin, InvenTreePlugin):
    """A basic wron plugin with urls"""

    NAME = "WrongIntegrationPlugin"
