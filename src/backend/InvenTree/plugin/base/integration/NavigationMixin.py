"""Plugin mixin classes."""

import structlog

from plugin.helpers import MixinNotImplementedError

logger = structlog.get_logger('inventree')


class NavigationMixin:
    """Mixin that enables custom navigation links with the plugin."""

    NAVIGATION_TAB_NAME = None
    NAVIGATION_TAB_ICON = 'fas fa-question'

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
        return getattr(self, 'NAVIGATION_TAB_ICON', 'fas fa-question')
