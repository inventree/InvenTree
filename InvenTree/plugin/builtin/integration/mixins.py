"""
Plugin mixin classes
"""

import logging

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

    # Override this in subclass model
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


class EventMixin:
    """
    Mixin that provides support for responding to triggered events.

    Implementing classes must provide a list of tuples,
    which provide pairs of 'event':'function'

    Notes:
    
    Events are called by name, and based on the django signal nomenclature,
    e.g. 'part.pre_save'
    
    Receiving functions must be prototyped to match the 'event' they receive.

    Example:

    EVENTS = [
        ('part.pre_save', 'myplugin.functions.do_stuff'),
        ('build.complete', 'myplugin.functions.process_completed_build'),
    ]
    """

    # Override this in subclass model
    EVENTS = []

    class MixinMeta:
        MIXIN_NAME = 'Events'

    def __init__(self):
        super().__init__()
        self.add_mixin('events', 'has_events', __class__)
        self.events = getattr(self, 'EVENTS', [])

        self.validate_events()

    @property
    def has_events(self):
        return bool(self.events) and len(self.events) > 0

    def validate_events(self):
        """
        Check that the provided event callbacks are valid
        """

        if not self.has_events:
            raise ValueError('EVENTS not defined')

        for pair in self.events:
            valid = True

            if len(pair) == 2:
                event = pair[0].strip()
                func = pair[1].strip()

                if len(event) == 0 or len(func) == 0:
                    valid = False
            else:
                valid = False

            if not valid:
                raise ValueError("Invalid event callback: " + str(pair))


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
