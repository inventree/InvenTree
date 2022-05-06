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

    def render_location_info(self, loc):
        """
        Demonstrate that we can render information particular to a page
        """
        return f"""
        <h5>Location Information</h5>
        <em>This location has no sublocations!</em>
        <ul>
        <li><b>Name</b>: {loc.name}</li>
        <li><b>Path</b>: {loc.pathstring}</li>
        </ul>
        """

    def get_custom_panels(self, view, request):

        """
        You can decide at run-time which custom panels you want to display!

        - Display on every page
        - Only on a single page or set of pages
        - Only for a specific instance (e.g. part)
        - Based on the user viewing the page!
        """

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
                        'title': 'Childless Location',
                        'icon': 'fa-user',
                        'content': self.render_location_info(loc),
                    })
            except:
                pass

        return panels
