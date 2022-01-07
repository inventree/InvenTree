"""
Sample plugin which responds to events
"""

from plugin import IntegrationPluginBase
from plugin.mixins import EventMixin


def on_part_saved(*args, **kwargs):
    """
    Simple function which responds to a triggered event
    """

    part_id = kwargs['part_id']
    print(f"func on_part_saved() - part: {part_id}")


class EventPlugin(EventMixin, IntegrationPluginBase):
    """
    A sample plugin which provides supports for triggered events
    """

    PLUGIN_NAME = "EventPlugin"
    PLUGIN_SLUG = "event"
    PLUGIN_TITLE = "Triggered Events"

    EVENTS = [
        ('part.saved', 'plugin.samples.integration.event_sample.on_part_saved'),
    ]
