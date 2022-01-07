"""
Sample plugin which supports task scheduling
"""

from plugin import IntegrationPluginBase
from plugin.mixins import ScheduleMixin


# Define some simple tasks to perform
def print_hello():
    print("Hello")


def print_world():
    print("World")


class ScheduledTaskPlugin(ScheduleMixin, IntegrationPluginBase):
    """
    A sample plugin which provides support for scheduled tasks
    """

    PLUGIN_NAME = "ScheduledTasksPlugin"
    PLUGIN_SLUG = "schedule"
    PLUGIN_TITLE = "Scheduled Tasks"

    SCHEDULED_TASKS = {
        'hello': {
            'func': 'plugin.samples.integration.scheduled_task.print_hello',
            'schedule': 'I',
            'minutes': 5,
        },
        'world': {
            'func': 'plugin.samples.integration.scheduled_task.print_hello',
            'schedule': 'H',
        }
    }