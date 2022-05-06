"""
Sample plugin which renders custom panels on certain pages
"""

from plugin import IntegrationPluginBase
from plugin.mixins import PanelMixin


class CustomPanelSample(PanelMixin, IntegrationPluginBase):
    """
    A sample plugin which renders some custom panels.
    """

    PLUGIN_NAME = "CustomPanelExample"
    PLUGIN_SLUG = "panel"
    PLUGIN_TITLE = "Custom Panel Example"

    def get_custom_panels(self, page, instance, request):

        print("get_custom_panels:")

        return []