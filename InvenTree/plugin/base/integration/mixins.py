"""Plugin mixin classes."""

import json as json_pkg
import logging

from django.db.utils import OperationalError, ProgrammingError
from django.urls import include, re_path

import requests

import InvenTree.helpers
from plugin.helpers import (MixinImplementationError, MixinNotImplementedError,
                            render_template, render_text)
from plugin.models import PluginConfig, PluginSetting
from plugin.registry import registry
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

    @property
    def has_settings(self):
        """Does this plugin use custom global settings."""
        return bool(self.settings)

    def get_setting(self, key):
        """Return the 'value' of the setting associated with this plugin."""
        return PluginSetting.get_setting(key, plugin=self)

    def set_setting(self, key, value, user=None):
        """Set plugin setting value by key."""
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

                if Schedule.objects.filter(name=task_name).exists():
                    # Scheduled task already exists - continue!
                    continue  # pragma: no cover

                logger.info(f"Adding scheduled task '{task_name}'")

                func_name = task['func'].strip()

                if '.' in func_name:
                    """Dotted notation indicates that we wish to run a globally defined function, from a specified Python module."""

                    Schedule.objects.create(
                        name=task_name,
                        func=func_name,
                        schedule_type=task['schedule'],
                        minutes=task.get('minutes', None),
                        repeats=task.get('repeats', -1),
                    )

                else:
                    """
                    Non-dotted notation indicates that we wish to call a 'member function' of the calling plugin.

                    This is managed by the plugin registry itself.
                    """

                    slug = self.plugin_slug()

                    Schedule.objects.create(
                        name=task_name,
                        func=registry.call_plugin_function,
                        args=f"'{slug}', '{func_name}'",
                        schedule_type=task['schedule'],
                        minutes=task.get('minutes', None),
                        repeats=task.get('repeats', -1),
                    )

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
            headers[self.API_TOKEN] = self.get_setting(self.API_TOKEN_SETTING)
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
