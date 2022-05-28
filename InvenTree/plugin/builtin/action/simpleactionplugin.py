"""Sample implementation for ActionMixin."""

from plugin import InvenTreePlugin
from plugin.mixins import ActionMixin


class SimpleActionPlugin(ActionMixin, InvenTreePlugin):
    """An EXTREMELY simple action plugin which demonstrates the capability of the ActionMixin class."""

    NAME = "SimpleActionPlugin"
    ACTION_NAME = "simple"

    def perform_action(self, user=None, data=None):
        print("Action plugin in action!")

    def get_info(self, user, data=None):
        return {
            "user": user.username,
            "hello": "world",
        }

    def get_result(self, user=None, data=None):
        return True
