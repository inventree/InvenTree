"""Sample of a broken python file that will be ignored on import."""

from plugin import InvenTreePlugin


class BrokenFileIntegrationPlugin(InvenTreePlugin):
    """An very broken plugin."""


aaa = bb  # noqa: F821
