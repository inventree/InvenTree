"""Import helper for events."""

from generic.events import BaseEventEnum
from plugin.base.event.events import process_event, register_event, trigger_event


class PluginEvents(BaseEventEnum):
    """Event enumeration for the Plugin app."""

    PLUGINS_LOADED = 'plugins_loaded'
    PLUGIN_ACTIVATED = 'plugin_activated'


__all__ = ['PluginEvents', 'process_event', 'register_event', 'trigger_event']
