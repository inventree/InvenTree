# -*- coding: utf-8 -*-
"""
Base Class for InvenTree plugins
"""

from django.db.utils import OperationalError, ProgrammingError
from django.utils.text import slugify


class InvenTreePlugin():
    """
    Base class for a plugin
    """

    def __init__(self):
        pass

    # Override the plugin name for each concrete plugin instance
    PLUGIN_NAME = ''

    PLUGIN_SLUG = ''

    PLUGIN_TITLE = ''

    def plugin_name(self):
        """
        Return the name of this plugin plugin
        """
        return self.PLUGIN_NAME

    def plugin_slug(self):

        slug = getattr(self, 'PLUGIN_SLUG', None)

        if slug is None:
            slug = self.plugin_name()

        return slugify(slug)

    def plugin_title(self):

        return self.PLUGIN_TITLE

    def plugin_config(self, raise_error=False):
        """
        Return the PluginConfig object associated with this plugin
        """

        try:
            import plugin.models

            cfg, _ = plugin.models.PluginConfig.objects.get_or_create(
                key=self.plugin_slug(),
                name=self.plugin_name(),
            )
        except (OperationalError, ProgrammingError) as error:
            cfg = None

            if raise_error:
                raise error

        return cfg
