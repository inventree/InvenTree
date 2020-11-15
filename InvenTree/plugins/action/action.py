# -*- coding: utf-8 -*-

import logging

import plugins.plugin as plugin


logger = logging.getLogger(__name__)


class ActionPlugin(plugin.InvenTreePlugin):
    """
    The ActionPlugin class is used to perform custom actions
    """

    ACTION_NAME = ""

    @classmethod
    def action_name(cls):
        """
        Return the action name for this plugin.
        If the ACTION_NAME parameter is empty,
        look at the PLUGIN_NAME instead.
        """
        action = cls.ACTION_NAME
        
        if not action:
            action = cls.PLUGIN_NAME
        
        return action

    def __init__(self, user, data=None):
        """
        An action plugin takes a user reference, and an optional dataset (dict)
        """
        plugin.InvenTreePlugin.__init__(self)

        self.user = user
        self.data = data

    def perform_action(self):
        """
        Override this method to perform the action!
        """
        pass

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


class SimpleActionPlugin(ActionPlugin):
    """
    An EXTREMELY simple action plugin which demonstrates
    the capability of the ActionPlugin class
    """

    PLUGIN_NAME = "SimpleActionPlugin"
    ACTION_NAME = "simple"

    def perform_action(self):
        print("Action plugin in action!")

    def get_info(self):
        return {
            "user": self.user.username,
            "hello": "world",
        }

    def get_result(self):
        return True
