"""Plugin mixin class for AppMixin."""
import logging
from importlib import reload
from typing import OrderedDict

from django.apps import apps
from django.conf import settings
from django.contrib import admin

from plugin.helpers import handle_error

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

    def _activate_mixin(self, plugins, force_reload=False, full_reload: bool = False):
        """Activate AppMixin plugins - add custom apps and reload.

        Args:
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
                    plugin_path = self._get_plugin_path(plugin)
                    if plugin_path not in settings.INSTALLED_APPS:
                        settings.INSTALLED_APPS += [plugin_path]
                        self.installed_apps += [plugin_path]
                        apps_changed = True
            # if apps were changed or force loading base apps -> reload
            if apps_changed or force_reload:
                # first startup or force loading of base apps -> registry is prob false
                if self.apps_loading or force_reload:
                    self.apps_loading = False
                    self._reload_apps(force_reload=True, full_reload=full_reload)
                else:
                    self._reload_apps(full_reload=full_reload)

                # rediscover models/ admin sites
                self._reregister_contrib_apps()

                # update urls - must be last as models must be registered for creating admin routes
                self._update_urls()

    def _deactivate_mixin(self):
        """Deactivate AppMixin plugins - some magic required."""
        # unregister models from admin
        for plugin_path in self.installed_apps:
            models = []  # the modelrefs need to be collected as poping an item in a iter is not welcomed
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
                logger.debug(f'{app_name} App was not found during deregistering')
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
        self._clean_installed_apps()

        # reset load flag and reload apps
        settings.INTEGRATION_APPS_LOADED = False
        self._reload_apps()

        # update urls to remove the apps from the site admin
        self._update_urls()

    # region helpers
    def _reregister_contrib_apps(self):
        """Fix reloading of contrib apps - models and admin.

        This is needed if plugins were loaded earlier and then reloaded as models and admins rely on imports.
        Those register models and admin in their respective objects (e.g. admin.site for admin).
        """
        for plugin_path in self.installed_apps:
            try:
                app_name = plugin_path.split('.')[-1]
                app_config = apps.get_app_config(app_name)
            except LookupError:  # pragma: no cover
                # the plugin was never loaded correctly
                logger.debug(f'{app_name} App was not found during deregistering')
                break

            # reload models if they were set
            # models_module gets set if models were defined - even after multiple loads
            # on a reload the models registery is empty but models_module is not
            if app_config.models_module and len(app_config.models) == 0:
                reload(app_config.models_module)

            # check for all models if they are registered with the site admin
            model_not_reg = False
            for model in app_config.get_models():
                if not admin.site.is_registered(model):
                    model_not_reg = True

            # reload admin if at least one model is not registered
            # models are registered with admin in the 'admin.py' file - so we check
            # if the app_config has an admin module before trying to laod it
            if model_not_reg and hasattr(app_config.module, 'admin'):
                reload(app_config.module.admin)

    def _get_plugin_path(self, plugin):
        """Parse plugin path.

        The input can be eiter:
        - a local file / dir
        - a package
        """
        try:
            # for local path plugins
            plugin_path = '.'.join(plugin.path().relative_to(settings.BASE_DIR).parts)
        except ValueError:  # pragma: no cover
            # plugin is shipped as package - extract plugin module name
            plugin_path = plugin.__module__.split('.')[0]
        return plugin_path

    def _try_reload(self, cmd, *args, **kwargs):
        """Wrapper to try reloading the apps.

        Throws an custom error that gets handled by the loading function.
        """
        try:
            cmd(*args, **kwargs)
            return True, []
        except Exception as error:  # pragma: no cover
            handle_error(error)

    def _reload_apps(self, force_reload: bool = False, full_reload: bool = False):
        """Internal: reload apps using django internal functions.

        Args:
            force_reload (bool, optional): Also reload base apps. Defaults to False.
            full_reload (bool, optional): Reload everything - including plugin mechanism. Defaults to False.
        """
        # If full_reloading is set to true we do not want to set the flag
        if not full_reload:
            self.is_loading = True  # set flag to disable loop reloading
        if force_reload:
            # we can not use the built in functions as we need to brute force the registry
            apps.app_configs = OrderedDict()
            apps.apps_ready = apps.models_ready = apps.loading = apps.ready = False
            apps.clear_cache()
            self._try_reload(apps.populate, settings.INSTALLED_APPS)
        else:
            self._try_reload(apps.set_installed_apps, settings.INSTALLED_APPS)
        self.is_loading = False
    # endregion

    @property
    def has_app(self):
        """This plugin is always an app with this plugin."""
        return True
