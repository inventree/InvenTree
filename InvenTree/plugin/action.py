# -*- coding: utf-8 -*-
"""Class for ActionPlugin"""

import logging
import warnings

import plugin.plugin as plugin
from plugin.builtin.action.mixins import ActionMixin
import plugin.integration


logger = logging.getLogger("inventree")


class ActionPlugin(ActionMixin, plugin.integration.IntegrationPluginBase):
    """
    Legacy action definition - will be replaced
    Please use the new Integration Plugin API and the Action mixin
    """
    def __init__(self, user=None, data=None):
        warnings.warn("using the ActionPlugin is depreceated", DeprecationWarning)
        super().__init__()
        self.init(user, data)
