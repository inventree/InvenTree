"""Attempt to create a bad actor plugin that overrides internal methods."""

from plugin import InvenTreePlugin


class BadActorPlugin(InvenTreePlugin):
    """A plugin that attempts to override internal methods."""

    SLUG = 'bad_actor'

    def __init__(self, *args, **kwargs):
        """Initialize the plugin."""
        super().__init__(*args, **kwargs)
        self.add_mixin('settings', 'has_settings', __class__)

    def plugin_slug(self) -> str:
        """Return the slug of this plugin."""
        return 'bad_actor'

    def plugin_name(self) -> str:
        """Return the name of this plugin."""
        return 'Bad Actor Plugin'
