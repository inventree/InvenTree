"""Sample of a broken plugin."""
from plugin import InvenTreePlugin


class BrokenIntegrationPlugin(InvenTreePlugin):
    """A very broken plugin."""

    NAME = 'Test'
    TITLE = 'Broken Plugin'
    SLUG = 'broken'

    def __init__(self):
        super().__init__()

        raise KeyError('This is a dummy error')
