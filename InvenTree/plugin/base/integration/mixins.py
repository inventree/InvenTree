"""Plugin mixin classes."""

import json as json_pkg
import logging
from importlib import reload
from typing import OrderedDict

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.db.utils import OperationalError, ProgrammingError
from django.urls import include, re_path

import requests

from plugin.helpers import (MixinImplementationError, MixinNotImplementedError,
                            handle_error, render_template, render_text)
from plugin.urls import PLUGIN_BASE

logger = logging.getLogger('inventree')


class SettingsMixin:
    """Mixin that enables global settings for the plugin."""

    class MixinMeta:
        """Meta for mixin."""
        MIXIN_NAME = 'Settings'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('settings', 'has_settings', __class__)
        self.settings = getattr(self, 'SETTINGS', {})

    def _activate_mixin(self, plugins, *args, **kwargs):
        """Activate plugin settings.

        Add all defined settings form the plugins to a unified dict in the registry.
        This dict is referenced by the PluginSettings for settings definitions.
        """
        logger.info('Activating plugin settings')

        self.mixins_settings = {}

        for slug, plugin in plugins:
            if plugin.mixin_enabled('settings'):
                plugin_setting = plugin.settings
                self.mixins_settings[slug] = plugin_setting

    def _deactivate_mixin(self):
        """Deactivate all plugin settings."""
        logger.info('Deactivating plugin settings')
        # clear settings cache
        self.mixins_settings = {}

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


class ScheduleMixin:
    """Mixin that provides support for scheduled tasks.

    Implementing classes must provide a dict object called SCHEDULED_TASKS,
    which provides information on the tasks to be scheduled.

    SCHEDULED_TASKS = {
        # Name of the task (will be prepended with the plugin name)
        'test_server': {
            'func': 'myplugin.tasks.test_server',   # Python function to call (no arguments!)
            'schedule': "I",                        # Schedule type (see django_q.Schedule)
            'minutes': 30,                          # Number of minutes (only if schedule type = Minutes)
            'repeats': 5,                           # Number of repeats (leave blank for 'forever')
        },
        'member_func': {
            'func': 'my_class_func',                # Note, without the 'dot' notation, it will call a class member function
            'schedule': "H",                        # Once per hour
        },
    }

    Note: 'schedule' parameter must be one of ['I', 'H', 'D', 'W', 'M', 'Q', 'Y']

    Note: The 'func' argument can take two different forms:
        - Dotted notation e.g. 'module.submodule.func' - calls a global function with the defined path
        - Member notation e.g. 'my_func' (no dots!) - calls a member function of the calling class
    """

    ALLOWABLE_SCHEDULE_TYPES = ['I', 'H', 'D', 'W', 'M', 'Q', 'Y']

    # Override this in subclass model
    SCHEDULED_TASKS = {}

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'Schedule'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.scheduled_tasks = self.get_scheduled_tasks()
        self.validate_scheduled_tasks()

        self.add_mixin('schedule', 'has_scheduled_tasks', __class__)

    def _activate_mixin(self, plugins, *args, **kwargs):
        """Activate scheudles from plugins with the ScheduleMixin."""
        logger.info('Activating plugin tasks')

        from common.models import InvenTreeSetting

        # List of tasks we have activated
        task_keys = []

        if settings.PLUGIN_TESTING or InvenTreeSetting.get_setting('ENABLE_PLUGINS_SCHEDULE'):

            for _key, plugin in plugins:

                if plugin.mixin_enabled('schedule'):

                    if plugin.is_active():
                        # Only active tasks for plugins which are enabled
                        plugin.register_tasks()
                        task_keys += plugin.get_task_names()

        if len(task_keys) > 0:
            logger.info(f"Activated {len(task_keys)} scheduled tasks")

        # Remove any scheduled tasks which do not match
        # This stops 'old' plugin tasks from accumulating
        try:
            from django_q.models import Schedule

            scheduled_plugin_tasks = Schedule.objects.filter(name__istartswith="plugin.")

            deleted_count = 0

            for task in scheduled_plugin_tasks:
                if task.name not in task_keys:
                    task.delete()
                    deleted_count += 1

            if deleted_count > 0:
                logger.info(f"Removed {deleted_count} old scheduled tasks")  # pragma: no cover
        except (ProgrammingError, OperationalError):
            # Database might not yet be ready
            logger.warning("activate_integration_schedule failed, database not ready")

    def _deactivate_mixin(self):
        """Deactivate ScheduleMixin.

        Currently nothing is done here.
        """
        pass

    def get_scheduled_tasks(self):
        """Returns `SCHEDULED_TASKS` context.

        Override if you want the scheduled tasks to be dynamic (influenced by settings for example).
        """
        return getattr(self, 'SCHEDULED_TASKS', {})

    @property
    def has_scheduled_tasks(self):
        """Are tasks defined for this plugin."""
        return bool(self.scheduled_tasks)

    def validate_scheduled_tasks(self):
        """Check that the provided scheduled tasks are valid."""
        if not self.has_scheduled_tasks:
            raise MixinImplementationError("SCHEDULED_TASKS not defined")

        for key, task in self.scheduled_tasks.items():

            if 'func' not in task:
                raise MixinImplementationError(f"Task '{key}' is missing 'func' parameter")

            if 'schedule' not in task:
                raise MixinImplementationError(f"Task '{key}' is missing 'schedule' parameter")

            schedule = task['schedule'].upper().strip()

            if schedule not in self.ALLOWABLE_SCHEDULE_TYPES:
                raise MixinImplementationError(f"Task '{key}': Schedule '{schedule}' is not a valid option")

            # If 'minutes' is selected, it must be provided!
            if schedule == 'I' and 'minutes' not in task:
                raise MixinImplementationError(f"Task '{key}' is missing 'minutes' parameter")

    def get_task_name(self, key):
        """Task name for key."""
        # Generate a 'unique' task name
        slug = self.plugin_slug()
        return f"plugin.{slug}.{key}"

    def get_task_names(self):
        """All defined task names."""
        # Returns a list of all task names associated with this plugin instance
        return [self.get_task_name(key) for key in self.scheduled_tasks.keys()]

    def register_tasks(self):
        """Register the tasks with the database."""
        try:
            from django_q.models import Schedule

            for key, task in self.scheduled_tasks.items():

                task_name = self.get_task_name(key)

                obj = {
                    'name': task_name,
                    'schedule_type': task['schedule'],
                    'minutes': task.get('minutes', None),
                    'repeats': task.get('repeats', -1),
                }

                func_name = task['func'].strip()

                if '.' in func_name:
                    """Dotted notation indicates that we wish to run a globally defined function, from a specified Python module."""
                    obj['func'] = func_name
                else:
                    """Non-dotted notation indicates that we wish to call a 'member function' of the calling plugin. This is managed by the plugin registry itself."""
                    slug = self.plugin_slug()
                    obj['func'] = 'plugin.registry.call_plugin_function'
                    obj['args'] = f"'{slug}', '{func_name}'"

                if Schedule.objects.filter(name=task_name).exists():
                    # Scheduled task already exists - update it!
                    logger.info(f"Updating scheduled task '{task_name}'")
                    instance = Schedule.objects.get(name=task_name)
                    for item in obj:
                        setattr(instance, item, obj[item])
                    instance.save()
                else:
                    logger.info(f"Adding scheduled task '{task_name}'")
                    # Create a new scheduled task
                    Schedule.objects.create(**obj)

        except (ProgrammingError, OperationalError):  # pragma: no cover
            # Database might not yet be ready
            logger.warning("register_tasks failed, database not ready")

    def unregister_tasks(self):
        """Deregister the tasks with the database."""
        try:
            from django_q.models import Schedule

            for key, _ in self.scheduled_tasks.items():

                task_name = self.get_task_name(key)

                try:
                    scheduled_task = Schedule.objects.get(name=task_name)
                    scheduled_task.delete()
                except Schedule.DoesNotExist:
                    pass
        except (ProgrammingError, OperationalError):  # pragma: no cover
            # Database might not yet be ready
            logger.warning("unregister_tasks failed, database not ready")


class ValidationMixin:
    """Mixin class that allows custom validation for various parts of InvenTree

    Custom generation and validation functionality can be provided for:

    - Part names
    - Part IPN (internal part number) values
    - Serial numbers
    - Batch codes

    Notes:
    - Multiple ValidationMixin plugins can be used simultaneously
    - The stub methods provided here generally return None (null value).
    - The "first" plugin to return a non-null value for a particular method "wins"
    - In the case of "validation" functions, all loaded plugins are checked until an exception is thrown

    Implementing plugins may override any of the following methods which are of interest.

    For 'validation' methods, there are three 'acceptable' outcomes:
    - The method determines that the value is 'invalid' and raises a django.core.exceptions.ValidationError
    - The method passes and returns None (the code then moves on to the next plugin)
    - The method passes and returns True (and no subsequent plugins are checked)

    """

    class MixinMeta:
        """Metaclass for this mixin"""
        MIXIN_NAME = "Validation"

    def __init__(self):
        """Register the mixin"""
        super().__init__()
        self.add_mixin('validation', True, __class__)

    def validate_part_name(self, name: str):
        """Perform validation on a proposed Part name

        Arguments:
            name: The proposed part name

        Returns:
            None or True

        Raises:
            ValidationError if the proposed name is objectionable
        """
        return None

    def validate_part_ipn(self, ipn: str):
        """Perform validation on a proposed Part IPN (internal part number)

        Arguments:
            ipn: The proposed part IPN

        Returns:
            None or True

        Raises:
            ValidationError if the proposed IPN is objectionable
        """
        return None

    def validate_batch_code(self, batch_code: str):
        """Validate the supplied batch code

        Arguments:
            batch_code: The proposed batch code (string)

        Returns:
            None or True

        Raises:
            ValidationError if the proposed batch code is objectionable
        """
        return None

    def generate_batch_code(self):
        """Generate a new batch code

        Returns:
            A new batch code (string) or None
        """
        return None

    def validate_serial_number(self, serial: str):
        """Validate the supplied serial number

        Arguments:
            serial: The proposed serial number (string)

        Returns:
            None or True

        Raises:
            ValidationError if the proposed serial is objectionable
        """
        return None

    def convert_serial_to_int(self, serial: str):
        """Convert a serial number (string) into an integer representation.

        This integer value is used for efficient sorting based on serial numbers.

        A plugin which implements this method can either return:

        - An integer based on the serial string, according to some algorithm
        - A fixed value, such that serial number sorting reverts to the string representation
        - None (null value) to let any other plugins perform the converrsion

        Note that there is no requirement for the returned integer value to be unique.

        Arguments:
            serial: Serial value (string)

        Returns:
            integer representation of the serial number, or None
        """
        return None

    def increment_serial_number(self, serial: str):
        """Return the next sequential serial based on the provided value.

        A plugin which implements this method can either return:

        - A string which represents the "next" serial number in the sequence
        - None (null value) if the next value could not be determined

        Arguments:
            serial: Current serial value (string)
        """
        return None


class UrlsMixin:
    """Mixin that enables custom URLs for the plugin."""

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'URLs'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('urls', 'has_urls', __class__)
        self.urls = self.setup_urls()

    def _activate_mixin(self, plugins, force_reload=False, full_reload: bool = False):
        """Activate UrlsMixin plugins - add custom urls .

        Args:
            plugins (dict): List of IntegrationPlugins that should be installed
            force_reload (bool, optional): Only reload base apps. Defaults to False.
            full_reload (bool, optional): Reload everything - including plugin mechanism. Defaults to False.
        """
        from common.models import InvenTreeSetting
        if settings.PLUGIN_TESTING or InvenTreeSetting.get_setting('ENABLE_PLUGINS_URL'):
            logger.info('Registering UrlsMixin Plugin')
            urls_changed = False
            # check whether an activated plugin extends UrlsMixin
            for _key, plugin in plugins:
                if plugin.mixin_enabled('urls'):
                    urls_changed = True
            # if apps were changed or force loading base apps -> reload
            if urls_changed or force_reload or full_reload:
                # update urls - must be last as models must be registered for creating admin routes
                self._update_urls()

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
        """Urlpatterns for this plugin."""
        if self.has_urls:
            return re_path(f'^{self.slug}/', include((self.urls, self.slug)), name=self.slug)
        return None

    @property
    def has_urls(self):
        """Does this plugin use custom urls."""
        return bool(self.urls)


class NavigationMixin:
    """Mixin that enables custom navigation links with the plugin."""

    NAVIGATION_TAB_NAME = None
    NAVIGATION_TAB_ICON = "fas fa-question"

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'Navigation Links'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('navigation', 'has_naviation', __class__)
        self.navigation = self.setup_navigation()

    def setup_navigation(self):
        """Setup navigation links for this plugin."""
        nav_links = getattr(self, 'NAVIGATION', None)
        if nav_links:
            # check if needed values are configured
            for link in nav_links:
                if False in [a in link for a in ('link', 'name', )]:
                    raise MixinNotImplementedError('Wrong Link definition', link)
        return nav_links

    @property
    def has_naviation(self):
        """Does this plugin define navigation elements."""
        return bool(self.navigation)

    @property
    def navigation_name(self):
        """Name for navigation tab."""
        name = getattr(self, 'NAVIGATION_TAB_NAME', None)
        if not name:
            name = self.human_name
        return name

    @property
    def navigation_icon(self):
        """Icon-name for navigation tab."""
        return getattr(self, 'NAVIGATION_TAB_ICON', "fas fa-question")


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


class APICallMixin:
    """Mixin that enables easier API calls for a plugin.

    Steps to set up:
    1. Add this mixin before (left of) SettingsMixin and PluginBase
    2. Add two settings for the required url and token/passowrd (use `SettingsMixin`)
    3. Save the references to keys of the settings in `API_URL_SETTING` and `API_TOKEN_SETTING`
    4. (Optional) Set `API_TOKEN` to the name required for the token by the external API - Defaults to `Bearer`
    5. (Optional) Override the `api_url` property method if the setting needs to be extended
    6. (Optional) Override `api_headers` to add extra headers (by default the token and Content-Type are contained)
    7. Access the API in you plugin code via `api_call`

    Example:
    ```
    from plugin import InvenTreePlugin
    from plugin.mixins import APICallMixin, SettingsMixin


    class SampleApiCallerPlugin(APICallMixin, SettingsMixin, InvenTreePlugin):
        '''
        A small api call sample
        '''
        NAME = "Sample API Caller"

        SETTINGS = {
            'API_TOKEN': {
                'name': 'API Token',
                'protected': True,
            },
            'API_URL': {
                'name': 'External URL',
                'description': 'Where is your API located?',
                'default': 'reqres.in',
            },
        }
        API_URL_SETTING = 'API_URL'
        API_TOKEN_SETTING = 'API_TOKEN'

        def get_external_url(self):
            '''
            returns data from the sample endpoint
            '''
            return self.api_call('api/users/2')
    ```
    """
    API_METHOD = 'https'
    API_URL_SETTING = None
    API_TOKEN_SETTING = None

    API_TOKEN = 'Bearer'

    class MixinMeta:
        """Meta options for this mixin."""
        MIXIN_NAME = 'API calls'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('api_call', 'has_api_call', __class__)

    @property
    def has_api_call(self):
        """Is the mixin ready to call external APIs?"""
        if not bool(self.API_URL_SETTING):
            raise MixinNotImplementedError("API_URL_SETTING must be defined")
        if not bool(self.API_TOKEN_SETTING):
            raise MixinNotImplementedError("API_TOKEN_SETTING must be defined")
        return True

    @property
    def api_url(self):
        """Base url path."""
        return f'{self.API_METHOD}://{self.get_setting(self.API_URL_SETTING)}'

    @property
    def api_headers(self):
        """Returns the default headers for requests with api_call.

        Contains a header with the key set in `API_TOKEN` for the plugin it `API_TOKEN_SETTING` is defined.
        Check the mixin class docstring for a full example.
        """
        headers = {'Content-Type': 'application/json'}
        if getattr(self, 'API_TOKEN_SETTING'):
            token = self.get_setting(self.API_TOKEN_SETTING)

            if token:
                headers[self.API_TOKEN] = token
                headers['Authorization'] = f"{self.API_TOKEN} {token}"

        return headers

    def api_build_url_args(self, arguments: dict) -> str:
        """Returns an encoded path for the provided dict."""
        groups = []
        for key, val in arguments.items():
            groups.append(f'{key}={",".join([str(a) for a in val])}')
        return f'?{"&".join(groups)}'

    def api_call(self, endpoint: str, method: str = 'GET', url_args: dict = None, data=None, json=None, headers: dict = None, simple_response: bool = True, endpoint_is_url: bool = False):
        """Do an API call.

        Simplest call example:
        ```python
        self.api_call('hello')
        ```
        Will call the `{base_url}/hello` with a GET request and - if set - the token for this plugin.

        Args:
            endpoint (str): Path to current endpoint. Either the endpoint or the full or if the flag is set
            method (str, optional): HTTP method that should be uses - capitalized. Defaults to 'GET'.
            url_args (dict, optional): arguments that should be appended to the url. Defaults to None.
            data (Any, optional): Data that should be transmitted in the body - url-encoded. Defaults to None.
            json (Any, optional): Data that should be transmitted in the body - must be JSON serializable. Defaults to None.
            headers (dict, optional): Headers that should be used for the request. Defaults to self.api_headers.
            simple_response (bool, optional): Return the response as JSON. Defaults to True.
            endpoint_is_url (bool, optional): The provided endpoint is the full url - do not use self.api_url as base. Defaults to False.

        Returns:
            Response
        """
        if url_args:
            endpoint += self.api_build_url_args(url_args)

        if headers is None:
            headers = self.api_headers

        if endpoint_is_url:
            url = endpoint
        else:

            if endpoint.startswith('/'):
                endpoint = endpoint[1:]

            url = f'{self.api_url}/{endpoint}'

        # build kwargs for call
        kwargs = {
            'url': url,
            'headers': headers,
        }

        if data and json:
            raise ValueError('You can either pass `data` or `json` to this function.')

        if json:
            kwargs['data'] = json_pkg.dumps(json)

        if data:
            kwargs['data'] = data

        # run command
        response = requests.request(method, **kwargs)

        # return
        if simple_response:
            return response.json()
        return response


class PanelMixin:
    """Mixin which allows integration of custom 'panels' into a particular page.

    The mixin provides a number of key functionalities:

    - Adds an (initially hidden) panel to the page
    - Allows rendering of custom templated content to the panel
    - Adds a menu item to the 'navbar' on the left side of the screen
    - Allows custom javascript to be run when the panel is initially loaded

    The PanelMixin class allows multiple panels to be returned for any page,
    and also allows the plugin to return panels for many different pages.

    Any class implementing this mixin must provide the 'get_custom_panels' method,
    which dynamically returns the custom panels for a particular page.

    This method is provided with:

    - view : The View object which is being rendered
    - request : The HTTPRequest object

    Note that as this is called dynamically (per request),
    then the actual panels returned can vary depending on the particular request or page

    The 'get_custom_panels' method must return a list of dict objects, each with the following keys:

    - title : The title of the panel, to appear in the sidebar menu
    - description : Extra descriptive text (optional)
    - icon : The icon to appear in the sidebar menu
    - content : The HTML content to appear in the panel, OR
    - content_template : A template file which will be rendered to produce the panel content
    - javascript : The javascript content to be rendered when the panel is loade, OR
    - javascript_template : A template file which will be rendered to produce javascript

    e.g.

    {
        'title': "Updates",
        'description': "Latest updates for this part",
        'javascript': 'alert("You just loaded this panel!")',
        'content': '<b>Hello world</b>',
    }
    """

    class MixinMeta:
        """Meta for mixin."""

        MIXIN_NAME = 'Panel'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('panel', True, __class__)

    def get_custom_panels(self, view, request):
        """This method *must* be implemented by the plugin class."""
        raise MixinNotImplementedError(f"{__class__} is missing the 'get_custom_panels' method")

    def get_panel_context(self, view, request, context):
        """Build the context data to be used for template rendering.

        Custom class can override this to provide any custom context data.

        (See the example in "custom_panel_sample.py")
        """
        # Provide some standard context items to the template for rendering
        context['plugin'] = self
        context['request'] = request
        context['user'] = getattr(request, 'user', None)
        context['view'] = view

        try:
            context['object'] = view.get_object()
        except AttributeError:  # pragma: no cover
            pass

        return context

    def render_panels(self, view, request, context):
        """Get panels for a view.

        Args:
            view: Current view context
            request: Current request for passthrough
            context: Rendering context

        Returns:
            Array of panels
        """
        import InvenTree.helpers

        panels = []

        # Construct an updated context object for template rendering
        ctx = self.get_panel_context(view, request, context)

        for panel in self.get_custom_panels(view, request):

            content_template = panel.get('content_template', None)
            javascript_template = panel.get('javascript_template', None)

            if content_template:
                # Render content template to HTML
                panel['content'] = render_template(self, content_template, ctx)
            else:
                # Render content string to HTML
                panel['content'] = render_text(panel.get('content', ''), ctx)

            if javascript_template:
                # Render javascript template to HTML
                panel['javascript'] = render_template(self, javascript_template, ctx)
            else:
                # Render javascript string to HTML
                panel['javascript'] = render_text(panel.get('javascript', ''), ctx)

            # Check for required keys
            required_keys = ['title', 'content']

            if any([key not in panel for key in required_keys]):
                logger.warning(f"Custom panel for plugin {__class__} is missing a required parameter")
                continue

            # Add some information on this plugin
            panel['plugin'] = self
            panel['slug'] = self.slug

            # Add a 'key' for the panel, which is mostly guaranteed to be unique
            panel['key'] = InvenTree.helpers.generateTestKey(self.slug + panel.get('title', 'panel'))

            panels.append(panel)

        return panels


class SettingsContentMixin:
    """Mixin which allows integration of custom HTML content into a plugins settings page.

    The 'get_settings_content' method must return the HTML content to appear in the section
    """

    class MixinMeta:
        """Meta for mixin."""

        MIXIN_NAME = 'SettingsContent'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('settingscontent', True, __class__)

    def get_settings_content(self, view, request):
        """This method *must* be implemented by the plugin class."""
        raise MixinNotImplementedError(f"{__class__} is missing the 'get_settings_content' method")
