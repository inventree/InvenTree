"""Model defintion for supplier mixin."""
from django.db import models
from django.utils.translation import gettext_lazy as _

import common.models
from plugin import registry
from plugin.models import PluginConfig


class ConnectionSetting(common.models.BaseInvenTreeSetting):
    """This model represents settings for an individual connection."""

    class Meta:
        """Meta for ConnectionSetting."""
        unique_together = [
            ('plugin', 'key'),
        ]

    plugin = models.ForeignKey(
        PluginConfig,
        related_name='connections',
        null=False,
        verbose_name=_('Plugin'),
        on_delete=models.CASCADE,
    )

    connection = models.CharField(
        unique=True,
        max_length=255,
        verbose_name=_('Connection'),
        help_text=_('connection'),
    )

    @classmethod
    def get_setting_definition(cls, key, **kwargs):
        """Overwritten settings definition loader. See PluginSettings as reference."""
        if 'settings' not in kwargs:

            plugin = kwargs.pop('plugin', None)
            connection = kwargs.pop('connection', None)

            if plugin and connection:
                plugin_connection_settings = registry.mixins_suppliers.get(plugin, None)
                if plugin_connection_settings:
                    connection_settings = plugin_connection_settings.get(connection, None)
                    if connection_settings:
                        kwargs['settings'] = connection_settings.settings

        return super().get_setting_definition(key, **kwargs)

    def get_kwargs(self):
        """Explicit kwargs required to uniquely identify a particular setting object, in addition to the 'key' parameter."""
        return {
            'plugin': self.plugin,
            'connection': self.connection,
        }
