# -*- coding: utf-8 -*-
"""Base Class for InvenTree plugins"""


from django.utils.text import slugify


class InvenTreePlugin():
    """
    Base class for a plugin
    """

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

    def __init__(self):
        pass
