# -*- coding: utf-8 -*-

import logging

from django.conf.urls import url, include
import plugins.plugin as plugin


logger = logging.getLogger("inventree")


class IntegrationPlugin(plugin.InvenTreePlugin):
    """
    The IntegrationPlugin class is used to integrate with 3rd party software
    """

    def __init__(self):
        """
        """
        plugin.InvenTreePlugin.__init__(self)

        self.urls = self.setup_urls()
        self.settings = self.setup_settings()

    def setup_urls(self):
        """
        setup url endpoints for this plugin
        """
        if self.urlpatterns:
            return self.urlpatterns
        return None

    @property
    def urlpatterns(self):
        """
        retruns the urlpatterns for this plugin
        """
        if self.has_urls:
            return url(f'^{self.plugin_name()}/', include(self.urls), name=self.plugin_name())
        return None

    @property
    def has_urls(self):
        """
        does this plugin use custom urls
        """
        return bool(self.urls)

    def setup_settings(self):
        """
        setup settings for this plugin
        """
        if self.SETTINGS:
            return self.SETTINGS
        return None

    @property
    def has_settings(self):
        """
        does this plugin use custom settings
        """
        return bool(self.settings)

    @property
    def settingspatterns(self):
        if self.has_settings:
            return {f'PLUGIN_{self.plugin_name().upper()}_{key}': value for key, value in self.settings.items()}
        return None
