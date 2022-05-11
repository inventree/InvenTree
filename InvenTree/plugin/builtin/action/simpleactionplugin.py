# -*- coding: utf-8 -*-
"""sample implementation for ActionMixin"""
from plugin import IntegrationPluginBase
from plugin.mixins import ActionMixin


class SimpleActionPlugin(ActionMixin, IntegrationPluginBase):
    """
    An EXTREMELY simple action plugin which demonstrates
    the capability of the ActionMixin class
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
