"""
Plugin mixin classes
"""

from django.conf.urls import url, include

from plugin.urls import PLUGIN_BASE


class SettingsMixin:
    """
    Mixin that enables global settings for the plugin
    """

    class MixinMeta:
        MIXIN_NAME = 'Settings'

    def __init__(self):
        super().__init__()
        self.add_mixin('settings', 'has_settings', __class__)
        self.globalsettings = getattr(self, 'SETTINGS', None)

    @property
    def has_settings(self):
        """
        Does this plugin use custom global settings
        """
        return bool(self.globalsettings)

    @property
    def globalsettingspatterns(self):
        """
        Get patterns for InvenTreeSetting defintion
        """
        if self.has_settings:
            return {f'PLUGIN_{self.slug.upper()}_{key}': value for key, value in self.globalsettings.items()}
        return None

    def _globalsetting_name(self, key):
        """
        Get global name of setting
        """
        return f'PLUGIN_{self.slug.upper()}_{key}'

    def get_globalsetting(self, key):
        """
        get plugin global setting by key
        """
        from common.models import InvenTreeSetting
        return InvenTreeSetting.get_setting(self._globalsetting_name(key))

    def set_globalsetting(self, key, value, user):
        """
        set plugin global setting by key
        """
        from common.models import InvenTreeSetting
        return InvenTreeSetting.set_setting(self._globalsetting_name(key), value, user)


class UrlsMixin:
    """
    Mixin that enables custom URLs for the plugin
    """

    class MixinMeta:
        MIXIN_NAME = 'URLs'

    def __init__(self):
        super().__init__()
        self.add_mixin('urls', 'has_urls', __class__)
        self.urls = self.setup_urls()

    def setup_urls(self):
        """
        setup url endpoints for this plugin
        """
        return getattr(self, 'URLS', None)

    @property
    def base_url(self):
        """
        returns base url for this plugin
        """
        return f'{PLUGIN_BASE}/{self.slug}/'

    @property
    def internal_name(self):
        """
        returns the internal url pattern name
        """
        return f'plugin:{self.slug}:'

    @property
    def urlpatterns(self):
        """
        returns the urlpatterns for this plugin
        """
        if self.has_urls:
            return url(f'^{self.slug}/', include((self.urls, self.slug)), name=self.slug)
        return None

    @property
    def has_urls(self):
        """
        does this plugin use custom urls
        """
        return bool(self.urls)


class NavigationMixin:
    """
    Mixin that enables custom navigation links with the plugin
    """

    NAVIGATION_TAB_NAME = None
    NAVIGATION_TAB_ICON = "fas fa-question"

    class MixinMeta:
        """meta options for this mixin"""
        MIXIN_NAME = 'Navigation Links'

    def __init__(self):
        super().__init__()
        self.add_mixin('navigation', 'has_naviation', __class__)
        self.navigation = self.setup_navigation()

    def setup_navigation(self):
        """
        setup navigation links for this plugin
        """
        nav_links = getattr(self, 'NAVIGATION', None)
        if nav_links:
            # check if needed values are configured
            for link in nav_links:
                if False in [a in link for a in ('link', 'name', )]:
                    raise NotImplementedError('Wrong Link definition', link)
        return nav_links

    @property
    def has_naviation(self):
        """
        does this plugin define navigation elements
        """
        return bool(self.navigation)

    @property
    def navigation_name(self):
        """name for navigation tab"""
        name = getattr(self, 'NAVIGATION_TAB_NAME', None)
        if not name:
            name = self.human_name
        return name

    @property
    def navigation_icon(self):
        """icon for navigation tab"""
        return getattr(self, 'NAVIGATION_TAB_ICON', "fas fa-question")


class AppMixin:
    """
    Mixin that enables full django app functions for a plugin
    """

    class MixinMeta:
        """meta options for this mixin"""
        MIXIN_NAME = 'App registration'

    def __init__(self):
        super().__init__()
        self.add_mixin('app', 'has_app', __class__)

    @property
    def has_app(self):
        """
        this plugin is always an app with this plugin
        """
        return True
