"""sample implementation for IntegrationPlugin"""
from plugin import InvenTreePlugin
from plugin.mixins import UrlsMixin


class NoIntegrationPlugin(InvenTreePlugin):
    """
    An basic integration plugin
    """

    PLUGIN_NAME = "NoIntegrationPlugin"


class WrongIntegrationPlugin(UrlsMixin, InvenTreePlugin):
    """
    An basic integration plugin
    """

    PLUGIN_NAME = "WrongIntegrationPlugin"
