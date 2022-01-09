"""
Plugin mixin classes for action plugin
"""

class ActionMixin:
    """
    Mixin that enables custom actions
    """
    ACTION_NAME = ""

    class MixinMeta:
        """
        meta options for this mixin
        """
        MIXIN_NAME = 'Actions'

    def __init__(self):
        super().__init__()
        self.add_mixin('action', 'has_action', __class__)

    @property
    def has_action(self):
        """
        Does this plugin have everything needed for an action?
        """
        return True

    def action_name(self):
        """
        Return the action name for this plugin.
        If the ACTION_NAME parameter is empty,
        look at the PLUGIN_NAME instead.
        """
        if self.ACTION_NAME:
            return self.ACTION_NAME
        return self.name

    def init(self, user, data=None):
        """
        An action plugin takes a user reference, and an optional dataset (dict)
        """
        self.user = user
        self.data = data

    def perform_action(self):
        """
        Override this method to perform the action!
        """

    def get_result(self):
        """
        Result of the action?
        """

        # Re-implement this for cutsom actions
        return False

    def get_info(self):
        """
        Extra info? Can be a string / dict / etc
        """
        return None

    def get_response(self):
        """
        Return a response. Default implementation is a simple response
        which can be overridden.
        """
        return {
            "action": self.action_name(),
            "result": self.get_result(),
            "info": self.get_info(),
        }
