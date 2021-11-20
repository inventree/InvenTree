"""sample implementation for IntegrationPlugin"""
from plugin.integration import IntegrationPluginBase

aaa = bb  # noqa: F821


class BrokenIntegrationPlugin(IntegrationPluginBase):
    """
    An very broken integration plugin
    """

    PLUGIN_NAME = "BrokenIntegrationPlugin"
