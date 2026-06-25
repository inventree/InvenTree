"""Plugin mixin class for UrlsMixin."""

from django.conf import settings

import structlog

from common.settings import get_global_setting
from plugin import PluginMixinEnum
from plugin.urls import PLUGIN_BASE

logger = structlog.get_logger('inventree')


class UrlsMixin:
    """Mixin that enables custom URLs for the plugin."""

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'URLs'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin(PluginMixinEnum.URLS, 'has_urls', __class__)
        self.urls = self.setup_urls()

    @classmethod
    def _activate_mixin(
        cls,
        registry,
        plugins,
        force_reload=False,
        full_reload: bool = False,
        *args,
        **kwargs,
    ):
        """Activate UrlsMixin plugins - add custom urls .

        Args:
            registry (PluginRegistry): The registry that should be used
            plugins (dict): List of IntegrationPlugins that should be installed
            force_reload (bool, optional): Only reload base apps. Defaults to False.
            full_reload (bool, optional): Reload everything - including plugin mechanism. Defaults to False.
        """
        if settings.PLUGIN_TESTING or get_global_setting('ENABLE_PLUGINS_URL'):
            logger.info('Registering UrlsMixin Plugin')
            urls_changed = False
            # check whether an activated plugin extends UrlsMixin
            for _key, plugin in plugins:
                if plugin.mixin_enabled(PluginMixinEnum.URLS):
                    urls_changed = True
            # if apps were changed or force loading base apps -> reload
            if urls_changed or force_reload or full_reload:
                # update urls - must be last as models must be registered for creating admin routes
                registry._update_urls()

    def setup_urls(self):
        """Setup url endpoints for this plugin."""
        return getattr(self, 'URLS', None)

    @property
    def base_url(self):
        """Base url for this plugin."""
        return f'{PLUGIN_BASE}/{self.slug}/'

    @property
    def internal_name(self):
        """Internal url pattern name."""
        return f'plugin:{self.slug}:'

    @property
    def urlpatterns(self):
        """URL patterns for this plugin."""
        return self.urls or None

    @property
    def has_urls(self):
        """Does this plugin use custom urls."""
        return bool(self.urls)
