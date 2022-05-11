"""
Sample plugin which responds to events
"""

from plugin import IntegrationPluginBase
from plugin.mixins import EventMixin


class EventPluginSample(EventMixin, IntegrationPluginBase):
    """
    A sample plugin which provides supports for triggered events
    """

    PLUGIN_NAME = "EventPlugin"
    PLUGIN_SLUG = "event"
    PLUGIN_TITLE = "Triggered Events"

    def process_event(self, event, *args, **kwargs):
        """ Custom event processing """

        print(f"Processing triggered event: '{event}'")
        print("args:", str(args))
        print("kwargs:", str(kwargs))
