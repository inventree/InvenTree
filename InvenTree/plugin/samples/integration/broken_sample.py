"""sample of a broken integration plugin"""
from plugin import InvenTreePlugin


class BrokenIntegrationPlugin(InvenTreePlugin):
    """
    An very broken integration plugin
    """
    PLUGIN_NAME = 'Test'
    PLUGIN_TITLE = 'Broken Plugin'
    PLUGIN_SLUG = 'broken'

    def __init__(self):
        super().__init__()

        raise KeyError('This is a dummy error')
