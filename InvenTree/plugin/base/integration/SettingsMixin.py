"""Plugin mixin class for SettingsMixin."""
import logging
from typing import TYPE_CHECKING, Dict

from django.db.utils import OperationalError, ProgrammingError

logger = logging.getLogger('inventree')

# import only for typechecking, otherwise this throws a model is unready error
if TYPE_CHECKING:
    from common.models import SettingsKeyType
else:
    class SettingsKeyType:
        """Dummy class, so that python throws no error"""
        pass


class SettingsMixin:
    """Mixin that enables global settings for the plugin."""

    SETTINGS: Dict[str, SettingsKeyType] = {}

    class MixinMeta:
        """Meta for mixin."""
        MIXIN_NAME = 'Settings'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('settings', 'has_settings', __class__)
        self.settings = getattr(self, 'SETTINGS', {})

    @classmethod
    def _activate_mixin(cls, registry, plugins, *args, **kwargs):
        """Activate plugin settings.

        Add all defined settings form the plugins to a unified dict in the registry.
        This dict is referenced by the PluginSettings for settings definitions.
        """
        logger.info('Activating plugin settings')

        registry.mixins_settings = {}

        for slug, plugin in plugins:
            if plugin.mixin_enabled('settings'):
                plugin_setting = plugin.settings
                registry.mixins_settings[slug] = plugin_setting

    @classmethod
    def _deactivate_mixin(cls, registry, **kwargs):
        """Deactivate all plugin settings."""
        logger.info('Deactivating plugin settings')
        # clear settings cache
        registry.mixins_settings = {}

    @property
    def has_settings(self):
        """Does this plugin use custom global settings."""
        return bool(self.settings)

    def get_setting(self, key, cache=False):
        """Return the 'value' of the setting associated with this plugin.

        Arguments:
            key: The 'name' of the setting value to be retrieved
            cache: Whether to use RAM cached value (default = False)
        """
        from plugin.models import PluginSetting

        return PluginSetting.get_setting(key, plugin=self, cache=cache)

    def set_setting(self, key, value, user=None):
        """Set plugin setting value by key."""
        from plugin.models import PluginConfig, PluginSetting

        try:
            plugin, _ = PluginConfig.objects.get_or_create(key=self.plugin_slug(), name=self.plugin_name())
        except (OperationalError, ProgrammingError):  # pragma: no cover
            plugin = None

        if not plugin:  # pragma: no cover
            # Cannot find associated plugin model, return
            logger.error(f"Plugin configuration not found for plugin '{self.slug}'")
            return

        PluginSetting.set_setting(key, value, user, plugin=plugin)
