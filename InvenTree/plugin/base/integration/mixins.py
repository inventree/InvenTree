"""Plugin mixin classes."""

import logging

from InvenTree.helpers import generateTestKey
from plugin.helpers import MixinNotImplementedError, render_template, render_text

logger = logging.getLogger('inventree')


class NavigationMixin:
    """Mixin that enables custom navigation links with the plugin."""

    NAVIGATION_TAB_NAME = None
    NAVIGATION_TAB_ICON = "fas fa-question"

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'Navigation Links'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('navigation', 'has_navigation', __class__)
        self.navigation = self.setup_navigation()

    def setup_navigation(self):
        """Setup navigation links for this plugin."""
        nav_links = getattr(self, 'NAVIGATION', None)
        if nav_links:
            # check if needed values are configured
            for link in nav_links:
                if False in [a in link for a in ('link', 'name')]:
                    raise MixinNotImplementedError('Wrong Link definition', link)
        return nav_links

    @property
    def has_navigation(self):
        """Does this plugin define navigation elements."""
        return bool(self.navigation)

    @property
    def navigation_name(self):
        """Name for navigation tab."""
        name = getattr(self, 'NAVIGATION_TAB_NAME', None)
        if not name:
            name = self.human_name
        return name

    @property
    def navigation_icon(self):
        """Icon-name for navigation tab."""
        return getattr(self, 'NAVIGATION_TAB_ICON', "fas fa-question")


class PanelMixin:
    """Mixin which allows integration of custom 'panels' into a particular page.

    The mixin provides a number of key functionalities:

    - Adds an (initially hidden) panel to the page
    - Allows rendering of custom templated content to the panel
    - Adds a menu item to the 'navbar' on the left side of the screen
    - Allows custom javascript to be run when the panel is initially loaded

    The PanelMixin class allows multiple panels to be returned for any page,
    and also allows the plugin to return panels for many different pages.

    Any class implementing this mixin must provide the 'get_custom_panels' method,
    which dynamically returns the custom panels for a particular page.

    This method is provided with:

    - view : The View object which is being rendered
    - request : The HTTPRequest object

    Note that as this is called dynamically (per request),
    then the actual panels returned can vary depending on the particular request or page

    The 'get_custom_panels' method must return a list of dict objects, each with the following keys:

    - title : The title of the panel, to appear in the sidebar menu
    - description : Extra descriptive text (optional)
    - icon : The icon to appear in the sidebar menu
    - content : The HTML content to appear in the panel, OR
    - content_template : A template file which will be rendered to produce the panel content
    - javascript : The javascript content to be rendered when the panel is loaded, OR
    - javascript_template : A template file which will be rendered to produce javascript

    e.g.

    {
        'title': "Updates",
        'description': "Latest updates for this part",
        'javascript': 'alert("You just loaded this panel!")',
        'content': '<b>Hello world</b>',
    }
    """

    class MixinMeta:
        """Meta for mixin."""

        MIXIN_NAME = 'Panel'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('panel', True, __class__)

    def get_custom_panels(self, view, request):
        """This method *must* be implemented by the plugin class."""
        raise MixinNotImplementedError(
            f"{__class__} is missing the 'get_custom_panels' method"
        )

    def get_panel_context(self, view, request, context):
        """Build the context data to be used for template rendering.

        Custom class can override this to provide any custom context data.

        (See the example in "custom_panel_sample.py")
        """
        # Provide some standard context items to the template for rendering
        context['plugin'] = self
        context['request'] = request
        context['user'] = getattr(request, 'user', None)
        context['view'] = view

        try:
            context['object'] = view.get_object()
        except AttributeError:  # pragma: no cover
            pass

        return context

    def render_panels(self, view, request, context):
        """Get panels for a view.

        Args:
            view: Current view context
            request: Current request for passthrough
            context: Rendering context

        Returns:
            Array of panels
        """
        panels = []

        # Construct an updated context object for template rendering
        ctx = self.get_panel_context(view, request, context)

        custom_panels = self.get_custom_panels(view, request) or []

        for panel in custom_panels:
            content_template = panel.get('content_template', None)
            javascript_template = panel.get('javascript_template', None)

            if content_template:
                # Render content template to HTML
                panel['content'] = render_template(self, content_template, ctx)
            else:
                # Render content string to HTML
                panel['content'] = render_text(panel.get('content', ''), ctx)

            if javascript_template:
                # Render javascript template to HTML
                panel['javascript'] = render_template(self, javascript_template, ctx)
            else:
                # Render javascript string to HTML
                panel['javascript'] = render_text(panel.get('javascript', ''), ctx)

            # Check for required keys
            required_keys = ['title', 'content']

            if any(key not in panel for key in required_keys):
                logger.warning(
                    "Custom panel for plugin %s is missing a required parameter",
                    __class__,
                )
                continue

            # Add some information on this plugin
            panel['plugin'] = self
            panel['slug'] = self.slug

            # Add a 'key' for the panel, which is mostly guaranteed to be unique
            panel['key'] = generateTestKey(self.slug + panel.get('title', 'panel'))

            panels.append(panel)

        return panels


class SettingsContentMixin:
    """Mixin which allows integration of custom HTML content into a plugins settings page.

    The 'get_settings_content' method must return the HTML content to appear in the section
    """

    class MixinMeta:
        """Meta for mixin."""

        MIXIN_NAME = 'SettingsContent'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('settingscontent', True, __class__)

    def get_settings_content(self, view, request):
        """This method *must* be implemented by the plugin class."""
        raise MixinNotImplementedError(
            f"{__class__} is missing the 'get_settings_content' method"
        )
