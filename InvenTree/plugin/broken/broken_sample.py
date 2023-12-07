"""Sample of a broken plugin."""
from plugin import InvenTreePlugin


class BrokenIntegrationPlugin(InvenTreePlugin):
    """A very broken plugin."""

    NAME = 'Test'
    TITLE = 'Broken Plugin'
    SLUG = 'broken'

    def __init__(self):
        """Raise a KeyError to provoke a range of unit tests and safety mechanisms in the plugin loading mechanism."""
        super().__init__()

        raise KeyError('This is a dummy error')
