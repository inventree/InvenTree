# -*- coding: utf-8 -*-
"""
Base Class for InvenTree plugins
"""
import warnings

from django.db.utils import OperationalError, ProgrammingError
from django.utils.text import slugify


class InvenTreePluginBase():
    """
    Base class for a plugin
    DO NOT USE THIS DIRECTLY, USE plugin.IntegrationPluginBase
    """

    def __init__(self):
        pass

    # Override the plugin name for each concrete plugin instance
    PLUGIN_NAME = ''

    PLUGIN_SLUG = None

    PLUGIN_TITLE = None

    def plugin_name(self):
        """
        Name of plugin
        """
        return self.PLUGIN_NAME

    def plugin_slug(self):
        """
        Slug of plugin
        If not set plugin name slugified
        """

        slug = getattr(self, 'PLUGIN_SLUG', None)

        if slug is None:
            slug = self.plugin_name()

        return slugify(slug.lower())

    def plugin_title(self):
        """
        Title of plugin
        """

        if self.PLUGIN_TITLE:
            return self.PLUGIN_TITLE
        else:
            return self.plugin_name()

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

    def is_active(self):
        """
        Return True if this plugin is currently active
        """

        cfg = self.plugin_config()

        if cfg:
            return cfg.active
        else:
            return False


# TODO @matmair remove after InvenTree 0.7.0 release
class InvenTreePlugin(InvenTreePluginBase):
    """
    This is here for leagcy reasons and will be removed in the next major release
    """
    def __init__(self):
        warnings.warn("Using the InvenTreePlugin is depreceated", DeprecationWarning)
        super().__init__()
