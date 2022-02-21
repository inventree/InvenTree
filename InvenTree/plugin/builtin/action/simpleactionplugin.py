# -*- coding: utf-8 -*-
"""sample implementation for ActionPlugin"""
from plugin.action import ActionPlugin


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
