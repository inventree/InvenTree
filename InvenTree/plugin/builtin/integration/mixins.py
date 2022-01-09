"""
Plugin mixin classes
"""

import logging
import json
import requests

from django.conf.urls import url, include
from django.db.utils import OperationalError, ProgrammingError

from plugin.models import PluginConfig, PluginSetting
from plugin.urls import PLUGIN_BASE


logger = logging.getLogger('inventree')


class SettingsMixin:
    """
    Mixin that enables global settings for the plugin
    """

    class MixinMeta:
        MIXIN_NAME = 'Settings'

    def __init__(self):
        super().__init__()
        self.add_mixin('settings', 'has_settings', __class__)
        self.settings = getattr(self, 'SETTINGS', {})

    @property
    def has_settings(self):
        """
        Does this plugin use custom global settings
        """
        return bool(self.settings)

    def get_setting(self, key):
        """
        Return the 'value' of the setting associated with this plugin
        """

        return PluginSetting.get_setting(key, plugin=self)

    def set_setting(self, key, value, user=None):
        """
        Set plugin setting value by key
        """

        try:
            plugin, _ = PluginConfig.objects.get_or_create(key=self.plugin_slug(), name=self.plugin_name())
        except (OperationalError, ProgrammingError):
            plugin = None

        if not plugin:
            # Cannot find associated plugin model, return
            return

        PluginSetting.set_setting(key, value, user, plugin=plugin)


class ScheduleMixin:
    """
    Mixin that provides support for scheduled tasks.

    Implementing classes must provide a dict object called SCHEDULED_TASKS,
    which provides information on the tasks to be scheduled.

    SCHEDULED_TASKS = {
        # Name of the task (will be prepended with the plugin name)
        'test_server': {
            'func': 'myplugin.tasks.test_server',   # Python function to call (no arguments!)
            'schedule': "I",                        # Schedule type (see django_q.Schedule)
            'minutes': 30,                          # Number of minutes (only if schedule type = Minutes)
            'repeats': 5,                           # Number of repeats (leave blank for 'forever')
        }
    }

    Note: 'schedule' parameter must be one of ['I', 'H', 'D', 'W', 'M', 'Q', 'Y']
    """

    ALLOWABLE_SCHEDULE_TYPES = ['I', 'H', 'D', 'W', 'M', 'Q', 'Y']

    SCHEDULED_TASKS = {}

    class MixinMeta:
        MIXIN_NAME = 'Schedule'

    def __init__(self):
        super().__init__()
        self.add_mixin('schedule', 'has_scheduled_tasks', __class__)
        self.scheduled_tasks = getattr(self, 'SCHEDULED_TASKS', {})

        self.validate_scheduled_tasks()

    @property
    def has_scheduled_tasks(self):
        return bool(self.scheduled_tasks)

    def validate_scheduled_tasks(self):
        """
        Check that the provided scheduled tasks are valid
        """

        if not self.has_scheduled_tasks:
            raise ValueError("SCHEDULED_TASKS not defined")

        for key, task in self.scheduled_tasks.items():

            if 'func' not in task:
                raise ValueError(f"Task '{key}' is missing 'func' parameter")

            if 'schedule' not in task:
                raise ValueError(f"Task '{key}' is missing 'schedule' parameter")

            schedule = task['schedule'].upper().strip()

            if schedule not in self.ALLOWABLE_SCHEDULE_TYPES:
                raise ValueError(f"Task '{key}': Schedule '{schedule}' is not a valid option")

            # If 'minutes' is selected, it must be provided!
            if schedule == 'I' and 'minutes' not in task:
                raise ValueError(f"Task '{key}' is missing 'minutes' parameter")

    def get_task_name(self, key):
        # Generate a 'unique' task name
        slug = self.plugin_slug()
        return f"plugin.{slug}.{key}"

    def get_task_names(self):
        # Returns a list of all task names associated with this plugin instance
        return [self.get_task_name(key) for key in self.scheduled_tasks.keys()]

    def register_tasks(self):
        """
        Register the tasks with the database
        """

        try:
            from django_q.models import Schedule

            for key, task in self.scheduled_tasks.items():

                task_name = self.get_task_name(key)

                # If a matching scheduled task does not exist, create it!
                if not Schedule.objects.filter(name=task_name).exists():

                    logger.info(f"Adding scheduled task '{task_name}'")

                    Schedule.objects.create(
                        name=task_name,
                        func=task['func'],
                        schedule_type=task['schedule'],
                        minutes=task.get('minutes', None),
                        repeats=task.get('repeats', -1),
                    )
        except (ProgrammingError, OperationalError):
            # Database might not yet be ready
            logger.warning("register_tasks failed, database not ready")

    def unregister_tasks(self):
        """
        Deregister the tasks with the database
        """

        try:
            from django_q.models import Schedule

            for key, task in self.scheduled_tasks.items():

                task_name = self.get_task_name(key)

                try:
                    scheduled_task = Schedule.objects.get(name=task_name)
                    scheduled_task.delete()
                except Schedule.DoesNotExist:
                    pass
        except (ProgrammingError, OperationalError):
            # Database might not yet be ready
            logger.warning("unregister_tasks failed, database not ready")


class UrlsMixin:
    """
    Mixin that enables custom URLs for the plugin
    """

    class MixinMeta:
        MIXIN_NAME = 'URLs'

    def __init__(self):
        super().__init__()
        self.add_mixin('urls', 'has_urls', __class__)
        self.urls = self.setup_urls()

    def setup_urls(self):
        """
        setup url endpoints for this plugin
        """
        return getattr(self, 'URLS', None)

    @property
    def base_url(self):
        """
        returns base url for this plugin
        """
        return f'{PLUGIN_BASE}/{self.slug}/'

    @property
    def internal_name(self):
        """
        returns the internal url pattern name
        """
        return f'plugin:{self.slug}:'

    @property
    def urlpatterns(self):
        """
        returns the urlpatterns for this plugin
        """
        if self.has_urls:
            return url(f'^{self.slug}/', include((self.urls, self.slug)), name=self.slug)
        return None

    @property
    def has_urls(self):
        """
        does this plugin use custom urls
        """
        return bool(self.urls)


class NavigationMixin:
    """
    Mixin that enables custom navigation links with the plugin
    """

    NAVIGATION_TAB_NAME = None
    NAVIGATION_TAB_ICON = "fas fa-question"

    class MixinMeta:
        """
        meta options for this mixin
        """
        MIXIN_NAME = 'Navigation Links'

    def __init__(self):
        super().__init__()
        self.add_mixin('navigation', 'has_naviation', __class__)
        self.navigation = self.setup_navigation()

    def setup_navigation(self):
        """
        setup navigation links for this plugin
        """
        nav_links = getattr(self, 'NAVIGATION', None)
        if nav_links:
            # check if needed values are configured
            for link in nav_links:
                if False in [a in link for a in ('link', 'name', )]:
                    raise NotImplementedError('Wrong Link definition', link)
        return nav_links

    @property
    def has_naviation(self):
        """
        does this plugin define navigation elements
        """
        return bool(self.navigation)

    @property
    def navigation_name(self):
        """name for navigation tab"""
        name = getattr(self, 'NAVIGATION_TAB_NAME', None)
        if not name:
            name = self.human_name
        return name

    @property
    def navigation_icon(self):
        """icon for navigation tab"""
        return getattr(self, 'NAVIGATION_TAB_ICON', "fas fa-question")


class AppMixin:
    """
    Mixin that enables full django app functions for a plugin
    """

    class MixinMeta:
        """meta options for this mixin"""
        MIXIN_NAME = 'App registration'

    def __init__(self):
        super().__init__()
        self.add_mixin('app', 'has_app', __class__)

    @property
    def has_app(self):
        """
        this plugin is always an app with this plugin
        """
        return True


class APICallMixin:
    """
    Mixin that enables easier API calls for a plugin

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
    from plugin import IntegrationPluginBase
    from plugin.mixins import APICallMixin, SettingsMixin


    class SampleApiCallerPlugin(APICallMixin, SettingsMixin, IntegrationPluginBase):
        '''
        A small api call sample
        '''
        PLUGIN_NAME = "Sample API Caller"

        SETTINGS = {
            'API_TOKEN': {
                'name': 'API Token',
                'protected': True,
            },
            'API_URL': {
                'name': 'External URL',
                'description': 'Where is your API located?',
                'default': 'https://reqres.in',
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
        """meta options for this mixin"""
        MIXIN_NAME = 'external API usage'

    def __init__(self):
        super().__init__()
        self.add_mixin('api_call', 'has_api_call', __class__)

    @property
    def has_api_call(self):
        """Is the mixin ready to call external APIs?"""
        # TODO check if settings are set
        return True

    @property
    def api_url(self):
        return f'{self.API_METHOD}://{self.get_globalsetting(self.API_URL_SETTING)}'

    @property
    def api_headers(self):
        return {
            self.API_TOKEN: self.get_globalsetting(self.API_TOKEN_SETTING),
            'Content-Type': 'application/json'
        }

    def api_build_url_args(self, arguments):
        groups = []
        for key, val in arguments.items():
            groups.append(f'{key}={",".join([str(a) for a in val])}')
        return f'?{"&".join(groups)}'

    def api_call(self, endpoint, method: str = 'GET', url_args=None, data=None, headers=None, simple_response: bool = True):
        if url_args:
            endpoint += self.api_build_url_args(url_args)

        if headers is None:
            headers = self.api_headers

        # build kwargs for call
        kwargs = {
            'url': f'{self.api_url}/{endpoint}',
            'headers': headers,
        }
        if data:
            kwargs['data'] = json.dumps(data)

        # run command
        response = requests.request(method, **kwargs)

        # return
        if simple_response:
            return response.json()
        return response
