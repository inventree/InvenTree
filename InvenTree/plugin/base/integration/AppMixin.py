"""Plugin mixin class for AppMixin."""
import logging
from importlib import reload
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.contrib import admin

from InvenTree.config import get_plugin_dir

logger = logging.getLogger('inventree')


class AppMixin:
    """Mixin that enables full django app functions for a plugin."""

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'App registration'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('app', 'has_app', __class__)

    @classmethod
    def _activate_mixin(cls, registry, plugins, force_reload=False, full_reload: bool = False):
        """Activate AppMixin plugins - add custom apps and reload.

        Args:
            registry (PluginRegistry): The registry that should be used
            plugins (dict): List of IntegrationPlugins that should be installed
            force_reload (bool, optional): Only reload base apps. Defaults to False.
            full_reload (bool, optional): Reload everything - including plugin mechanism. Defaults to False.
        """
        from common.models import InvenTreeSetting

        if settings.PLUGIN_TESTING or InvenTreeSetting.get_setting('ENABLE_PLUGINS_APP'):
            logger.info('Registering IntegrationPlugin apps')
            apps_changed = False

            # add them to the INSTALLED_APPS
            for _key, plugin in plugins:
                if plugin.mixin_enabled('app'):
                    plugin_path = cls._get_plugin_path(plugin)
                    if plugin_path not in settings.INSTALLED_APPS:
                        settings.INSTALLED_APPS += [plugin_path]
                        registry.installed_apps += [plugin_path]
                        apps_changed = True

            # if apps were changed or force loading base apps -> reload
            # Ignore reloading if we are in testing mode and apps are unchanged so that tests run faster
            # registry.reload_plugins(...) first unloads and then loads the plugins
            # always reload if we are not in testing mode so we can expect the second reload
            if not settings.TESTING or apps_changed or force_reload:
                # first startup or force loading of base apps -> registry is prob false
                if registry.apps_loading or force_reload:
                    registry.apps_loading = False
                    registry._reload_apps(force_reload=True, full_reload=full_reload)
                else:
                    registry._reload_apps(full_reload=full_reload)

                # rediscover models/ admin sites
                cls._reregister_contrib_apps(cls, registry)

                # update urls - must be last as models must be registered for creating admin routes
                registry._update_urls()

    @classmethod
    def _deactivate_mixin(cls, registry, force_reload: bool = False):
        """Deactivate AppMixin plugins - some magic required.

        Args:
            registry (PluginRegistry): The registry that should be used
            force_reload (bool, optional): Also reload base apps. Defaults to False.
        """
        # unregister models from admin
        for plugin_path in registry.installed_apps:
            models = []  # the modelrefs need to be collected as popping an item in a iter is not welcomed
            app_name = plugin_path.split('.')[-1]
            try:
                app_config = apps.get_app_config(app_name)

                # check all models
                for model in app_config.get_models():
                    # remove model from admin site
                    try:
                        admin.site.unregister(model)
                    except Exception:  # pragma: no cover
                        pass
                    models += [model._meta.model_name]
            except LookupError:  # pragma: no cover
                # if an error occurs the app was never loaded right -> so nothing to do anymore
                logger.debug('%s App was not found during deregistering', app_name)
                break

            # unregister the models (yes, models are just kept in multilevel dicts)
            for model in models:
                # remove model from general registry
                apps.all_models[plugin_path].pop(model)

            # clear the registry for that app
            # so that the import trick will work on reloading the same plugin
            # -> the registry is kept for the whole lifecycle
            if models and app_name in apps.all_models:
                apps.all_models.pop(app_name)

        # remove plugin from installed_apps
        registry._clean_installed_apps()

        # reset load flag and reload apps
        settings.INTEGRATION_APPS_LOADED = False
        registry._reload_apps(force_reload=force_reload)

        # update urls to remove the apps from the site admin
        registry._update_urls()

    # region helpers
    def _reregister_contrib_apps(self, registry):
        """Fix reloading of contrib apps - models and admin.

        This is needed if plugins were loaded earlier and then reloaded as models and admins rely on imports.
        Those register models and admin in their respective objects (e.g. admin.site for admin).
        """
        for plugin_path in registry.installed_apps:
            try:
                app_name = plugin_path.split('.')[-1]
                app_config = apps.get_app_config(app_name)
            except LookupError:  # pragma: no cover
                # the plugin was never loaded correctly
                logger.debug('%s App was not found during deregistering', app_name)
                break

            # reload models if they were set
            # models_module gets set if models were defined - even after multiple loads
            # on a reload the models registry is empty but models_module is not
            if app_config.models_module and len(app_config.models) == 0:
                reload(app_config.models_module)

            # check for all models if they are registered with the site admin
            model_not_reg = False
            for model in app_config.get_models():
                if not admin.site.is_registered(model):
                    model_not_reg = True

            # reload admin if at least one model is not registered
            # models are registered with admin in the 'admin.py' file - so we check
            # if the app_config has an admin module before trying to load it
            if model_not_reg and hasattr(app_config.module, 'admin'):
                reload(app_config.module.admin)

    @classmethod
    def _get_plugin_path(cls, plugin):
        """Parse plugin path.

        The input can be either:
        - a local file / dir
        - a package
        """
        path = plugin.path()
        custom_plugins_dir = get_plugin_dir()

        if path.is_relative_to(settings.BASE_DIR):
            # Plugins which are located relative to the base code directory
            plugin_path = '.'.join(path.relative_to(settings.BASE_DIR).parts)
        elif custom_plugins_dir and path.is_relative_to(custom_plugins_dir):
            # Plugins which are located relative to the custom plugins directory
            plugin_path = '.'.join(path.relative_to(custom_plugins_dir).parts)

            # Ensure that the parent directory is added also
            plugin_path = Path(custom_plugins_dir).parts[-1] + '.' + plugin_path
        else:
            # plugin is shipped as package - extract plugin module name
            plugin_path = plugin.__module__.split('.')[0]

        return plugin_path

# endregion

    @property
    def has_app(self):
        """This plugin is always an app with this plugin."""
        return True
