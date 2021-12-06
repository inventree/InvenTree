"""sample of a broken python file that will be ignored on import"""
from plugin import IntegrationPluginBase


class BrokenFileIntegrationPlugin(IntegrationPluginBase):
    """
    An very broken integration plugin
    """


aaa = bb  # noqa: F821
