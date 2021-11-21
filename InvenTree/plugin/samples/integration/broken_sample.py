"""sample of a broken integration plugin"""
from plugin import IntegrationPluginBase


class BrokenIntegrationPlugin(IntegrationPluginBase):
    """
    An very broken integration plugin
    """
    PLUGIN_TITLE = 'Broken Plugin'
    PLUGIN_SLUG = 'broken'

    def __init__(self):
        super().__init__()

        raise KeyError('This is a dummy error')
