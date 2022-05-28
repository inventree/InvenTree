"""Plugin mixin classes for action plugin"""


class ActionMixin:
    """Mixin that enables custom actions"""

    ACTION_NAME = ""

    class MixinMeta:
        """Meta options for this mixin"""

        MIXIN_NAME = 'Actions'

    def __init__(self):
        super().__init__()
        self.add_mixin('action', True, __class__)

    def action_name(self):
        """Action name for this plugin.

        If the ACTION_NAME parameter is empty,
        uses the NAME instead.
        """
        if self.ACTION_NAME:
            return self.ACTION_NAME
        return self.name

    def perform_action(self, user=None, data=None):
        """Override this method to perform the action!"""

    def get_result(self, user=None, data=None):
        """Result of the action?"""
        # Re-implement this for cutsom actions
        return False

    def get_info(self, user=None, data=None):
        """Extra info? Can be a string / dict / etc"""
        return None

    def get_response(self, user=None, data=None):
        """Return a response.

        Default implementation is a simple response which can be overridden.
        """
        return {
            "action": self.action_name(),
            "result": self.get_result(user, data),
            "info": self.get_info(user, data),
        }
