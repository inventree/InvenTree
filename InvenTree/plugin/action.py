# -*- coding: utf-8 -*-
"""Class for ActionPlugin"""

import logging
import warnings

import plugin.plugin as plugin_base
from plugin.builtin.action.mixins import ActionMixin
import plugin.integration


logger = logging.getLogger("inventree")


class ActionPlugin(ActionMixin, plugin_base.integration.IntegrationPluginBase):
    """
    Legacy action definition - will be replaced
    Please use the new Integration Plugin API and the Action mixin
    """
    # TODO @matmair remove this with InvenTree 0.7.0
    def __init__(self, user=None, data=None):
        warnings.warn("using the ActionPlugin is depreceated", DeprecationWarning)
        super().__init__()
        self.init(user, data)
