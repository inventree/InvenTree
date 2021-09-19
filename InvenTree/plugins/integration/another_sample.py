from plugins.integration.integration import IntegrationPlugin, UrlsMixin


class NoIntegrationPlugin(IntegrationPlugin):
    """
    An basic integration plugin
    """

    PLUGIN_NAME = "NoIntegrationPlugin"


class WrongIntegrationPlugin(UrlsMixin, IntegrationPlugin):
    """
    An basic integration plugin
    """

    PLUGIN_NAME = "WrongIntegrationPlugin"
