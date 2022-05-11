"""sample of a broken integration plugin"""
from plugin import InvenTreePlugin


class BrokenIntegrationPlugin(InvenTreePlugin):
    """
    An very broken integration plugin
    """
    NAME = 'Test'
    TITLE = 'Broken Plugin'
    SLUG = 'broken'

    def __init__(self):
        super().__init__()

        raise KeyError('This is a dummy error')
