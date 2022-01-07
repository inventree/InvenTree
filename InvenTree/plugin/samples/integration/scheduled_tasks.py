"""
Sample plugin which supports task scheduling
"""

from plugin import IntegrationPluginBase
from plugin.mixins import ScheduleMixin


class ScheduledTaskPlugin(ScheduleMixin, IntegrationPluginBase):
    """
    A sample plugin which provides support for scheduled tasks
    """

    PLUGIN_NAME = "ScheduledTasksPlugin"
    PLUGIN_SLUG = "schedule"
    PLUGIN_TITLE = "A plugin which provides scheduled task support"
