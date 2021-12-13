"""default mixins for IntegrationMixins"""
import json
import requests

from django.conf.urls import url, include

from plugin.urls import PLUGIN_BASE


class GlobalSettingsMixin:
    """Mixin that enables global settings for the plugin"""
    class MixinMeta:
        """meta options for this mixin"""
        MIXIN_NAME = 'Global settings'

    def __init__(self):
        super().__init__()
        self.add_mixin('globalsettings', 'has_globalsettings', __class__)
        self.globalsettings = self.setup_globalsettings()

    def setup_globalsettings(self):
        """
        setup global settings for this plugin
        """
        return getattr(self, 'GLOBALSETTINGS', None)

    @property
    def has_globalsettings(self):
        """
        does this plugin use custom global settings
        """
        return bool(self.globalsettings)

    @property
    def globalsettingspatterns(self):
        """
        get patterns for InvenTreeSetting defintion
        """
        if self.has_globalsettings:
            return {f'PLUGIN_{self.slug.upper()}_{key}': value for key, value in self.globalsettings.items()}
        return None

    def _globalsetting_name(self, key):
        """get global name of setting"""
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
    """Mixin that enables urls for the plugin"""
    class MixinMeta:
        """meta options for this mixin"""
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
    """Mixin that enables adding navigation links with the plugin"""
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
    """Mixin that enables full django app functions for a plugin"""
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


class APICallMixin:
    """Mixin that enables easier API calls for a plugin
    
    1. Add this mixin
    2. Add two global settings for the required url and token/passowrd (use `GlobalSettingsMixin`)
    3. Save the references to `API_URL_SETTING` and `API_PASSWORD_SETTING`
    4. Set `API_TOKEN` to the name required for the token / password by the external API
    5. (Optional) Override the `api_url` property method if some part of the APIs url is static
    6. (Optional) Override `api_headers` to add extra headers (by default the token/password and Content-Type are contained)
    6. Access the API in you plugin code via `api_call`
    """
    API_METHOD = 'https'
    API_URL_SETTING = None
    API_PASSWORD_SETTING = None

    API_TOKEN = 'Bearer'

    class MixinMeta:
        """meta options for this mixin"""
        MIXIN_NAME = 'external API usage'

    def __init__(self):
        super().__init__()
        self.add_mixin('api_call', 'has_api_call', __class__)

    @property
    def has_api_call(self):
        """Is the mixin ready to call external APIs?"""
        # TODO check if settings are set
        return True

    @property
    def api_url(self):
        return f'{self.API_METHOD}://{self.get_globalsetting(self.API_URL_SETTING)}'

    @property
    def api_headers(self):
        return {self.API_TOKEN: self.get_globalsetting(self.API_PASSWORD_SETTING), 'Content-Type': 'application/json'}

    def api_build_url_args(self, arguments):
        groups = []
        for key, val in arguments.items():
            groups.append(f'{key}={",".join([str(a) for a in val])}')
        return f'?{"&".join(groups)}'

    def api_call(self, endpoint, method: str='GET', url_args=None, data=None, headers=None, simple_response: bool = True):
        if url_args:
            endpoint += self.api_build_url_args(url_args)

        if headers is None:
            headers = self.api_headers

        # build kwargs for call
        kwargs = {
            'url': f'{self.api_url}/{endpoint}',
            'headers': headers,
        }
        if data:
            kwargs['data'] = json.dumps(data)

        # run command
        response = requests.request(method, **kwargs)

        # return
        if simple_response:
            return response.json()
        return response
