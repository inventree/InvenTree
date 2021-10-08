"""sample implementation for IntegrationPlugin"""
from plugin.integration import IntegrationPluginBase, UrlsMixin


class NoIntegrationPlugin(IntegrationPluginBase):
    """
    An basic integration plugin
    """

    PLUGIN_NAME = "NoIntegrationPlugin"


class WrongIntegrationPlugin(UrlsMixin, IntegrationPluginBase):
    """
    An basic integration plugin
    """

    PLUGIN_NAME = "WrongIntegrationPlugin"
