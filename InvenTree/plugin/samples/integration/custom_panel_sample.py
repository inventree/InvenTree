"""
Sample plugin which renders custom panels on certain pages
"""

from plugin import IntegrationPluginBase
from plugin.mixins import PanelMixin

from part.views import PartDetail
from stock.views import StockLocationDetail


class CustomPanelSample(PanelMixin, IntegrationPluginBase):
    """
    A sample plugin which renders some custom panels.
    """

    PLUGIN_NAME = "CustomPanelExample"
    PLUGIN_SLUG = "panel"
    PLUGIN_TITLE = "Custom Panel Example"

    def get_custom_panels(self, view, request):

        panels = [
            {
                # This 'hello world' panel will be displayed on any view which implements custom panels
                'title': 'Hello World',
                'icon': 'fas fa-boxes',
                'content': '<b>Hello world!</b>',
                'description': 'A simple panel which renders hello world',
                'javascript': 'alert("Hello world");',
            },
            {
                # This panel will not be displayed, as it is missing the 'content' key
                'title': 'No Content',
            }
        ]

        # This panel will *only* display on the PartDetail view
        if isinstance(view, PartDetail):
            panels.append({
                'title': 'Custom Part Panel',
                'icon': 'fas fa-shapes',
                'content': '<em>This content only appears on the PartDetail page, you know!</em>',
            })

        # This panel will *only* display on the StockLocation view,
        # and *only* if the StockLocation has *no* child locations
        if isinstance(view, StockLocationDetail):
            try:
                loc = view.get_object()

                if not loc.get_descendants(include_self=False).exists():
                    panels.append({
                        'title': 'Childless',
                        'icon': 'fa-user',
                        'content': '<h4>I have no children!</h4>'
                    })
            except:
                pass

        return panels
