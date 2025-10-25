"""Helper functions for pricing support."""

from common.settings import get_global_setting
from plugin import PluginMixinEnum, registry
from plugin.models import InvenTreePlugin


def get_pricing_plugin() -> InvenTreePlugin:
    """Return the selected pricing plugin.

    Attempts to retrieve the currently selected pricing plugin from the plugin registry.
    If the plugin is not available, or is disabled,
    then return the default InvenTreePricing plugin.
    """
    default_slug = 'inventree-pricing'

    plugin_slug = get_global_setting('PRICING_PLUGIN', backup_value=default_slug)

    plugin = registry.get_plugin(plugin_slug, with_mixin=PluginMixinEnum.PRICING)

    if plugin is None:
        plugin = registry.get_plugin(default_slug, with_mixin=PluginMixinEnum.PRICING)

    # TODO: Handle case where default plugin is missing?

    return plugin
