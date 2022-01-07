"""
Plugin mixin classes
"""

from django.conf.urls import url, include
from django.db.utils import OperationalError, ProgrammingError

from plugin.models import PluginConfig, PluginSetting
from plugin.urls import PLUGIN_BASE


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
            raise ValueError(f"SCHEDULED_TASKS not defined")

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
