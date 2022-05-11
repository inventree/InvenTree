"""
Sample plugin which renders custom panels on certain pages
"""

from plugin import InvenTreePlugin
from plugin.mixins import PanelMixin, SettingsMixin

from part.views import PartDetail
from stock.views import StockLocationDetail


class CustomPanelSample(PanelMixin, SettingsMixin, InvenTreePlugin):
    """
    A sample plugin which renders some custom panels.
    """

    PLUGIN_NAME = "CustomPanelExample"
    PLUGIN_SLUG = "panel"
    PLUGIN_TITLE = "Custom Panel Example"
    DESCRIPTION = "An example plugin demonstrating how custom panels can be added to the user interface"
    VERSION = "0.1"

    SETTINGS = {
        'ENABLE_HELLO_WORLD': {
            'name': 'Hello World',
            'description': 'Enable a custom hello world panel on every page',
            'default': False,
            'validator': bool,
        }
    }

    def get_panel_context(self, view, request, context):

        ctx = super().get_panel_context(view, request, context)

        # If we are looking at a StockLocationDetail view, add location context object
        if isinstance(view, StockLocationDetail):
            ctx['location'] = view.get_object()

        return ctx

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
                # This panel will not be displayed, as it is missing the 'content' key
                'title': 'No Content',
            }
        ]

        if self.get_setting('ENABLE_HELLO_WORLD'):
            panels.append({
                # This 'hello world' panel will be displayed on any view which implements custom panels
                'title': 'Hello World',
                'icon': 'fas fa-boxes',
                'content': '<b>Hello world!</b>',
                'description': 'A simple panel which renders hello world',
                'javascript': 'console.log("Hello world, from a custom panel!");',
            })

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
                        'content_template': 'panel_demo/childless.html',  # Note that the panel content is rendered using a template file!
                    })
            except:
                pass

        return panels
