"""sample of a broken python file that will be ignroed on import"""
from plugin.integration import IntegrationPluginBase


class BrokenIntegrationPlugin(IntegrationPluginBase):
    """
    An very broken integration plugin
    """


aaa = bb  # noqa: F821
