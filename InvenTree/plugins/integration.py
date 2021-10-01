# -*- coding: utf-8 -*-
"""class for IntegrationPlugin and Mixins for it"""

import logging
import os
import subprocess
import inspect

from django.conf.urls import url, include
from django.conf import settings

import plugins.plugin as plugin


logger = logging.getLogger("inventree")


# region mixins
class MixinBase:
    """general base for mixins"""

    def __init__(self) -> None:
        self._mixinreg = {}
        self._mixins = {}

    def add_mixin(self, key: str, fnc_enabled=True, cls=None):
        """add a mixin to the plugins registry"""
        self._mixins[key] = fnc_enabled
        self.setup_mixin(key, cls=cls)

    def setup_mixin(self, key, cls=None):
        """define mixin details for the current mixin -> provides meta details for all active mixins"""
        # get human name
        human_name = getattr(cls.Meta, 'MIXIN_NAME', key) if cls and hasattr(cls, 'Meta') else key

        # register
        self._mixinreg[key] = {
            'key': key,
            'human_name': human_name,
        }

    @property
    def registered_mixins(self, with_base: bool = False):
        """get all registered mixins for the plugin"""
        mixins = getattr(self, '_mixinreg', None)
        if mixins:
            # filter out base
            if not with_base and 'base' in mixins:
                del mixins['base']
            # only return dict
            mixins = [a for a in mixins.values()]
        return mixins


class SettingsMixin:
    """Mixin that enables settings for the plugin"""
    class Meta:
        """meta options for this mixin"""
        MIXIN_NAME = 'Settings'

    def __init__(self):
        super().__init__()
        self.add_mixin('settings', 'has_settings', __class__)
        self.settings = self.setup_settings()

    def setup_settings(self):
        """
        setup settings for this plugin
        """
        return getattr(self, 'SETTINGS', None)

    @property
    def has_settings(self):
        """
        does this plugin use custom settings
        """
        return bool(self.settings)

    @property
    def settingspatterns(self):
        """
        get patterns for InvenTreeSetting defintion
        """
        if self.has_settings:
            return {f'PLUGIN_{self.plugin_name().upper()}_{key}': value for key, value in self.settings.items()}
        return None

    def get_setting(self, key):
        """
        get plugin setting by key
        """
        from common.models import InvenTreeSetting
        return InvenTreeSetting.get_setting(f'PLUGIN_{self.PLUGIN_NAME.upper()}_{key}')


class UrlsMixin:
    """Mixin that enables urls for the plugin"""
    class Meta:
        """meta options for this mixin"""
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
        return f'{settings.PLUGIN_URL}/{self.plugin_name()}/'

    @property
    def urlpatterns(self):
        """
        returns the urlpatterns for this plugin
        """
        if self.has_urls:
            return url(f'^{self.plugin_name()}/', include((self.urls, self.plugin_name())), name=self.plugin_name())
        return None

    @property
    def has_urls(self):
        """
        does this plugin use custom urls
        """
        return bool(self.urls)


class NavigationMixin:
    """Mixin that enables adding navigation links with the plugin"""
    class Meta:
        """meta options for this mixin"""
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
# endregion


# region git-helpers
def get_git_log(path):
    """get dict with info of the last commit to file named in path"""
    path = path.replace(os.path.dirname(settings.BASE_DIR), '')[1:]
    command = ['git', 'log', '-n', '1', "--pretty=format:'%H%n%aN%n%aE%n%aI%n%f%n%G?%n%GK'", '--follow', '--', path]
    try:
        output = str(subprocess.check_output(command, cwd=os.path.dirname(settings.BASE_DIR)), 'utf-8')[1:-1]
        if output:
            output = output.split('\n')
        else:
            output = 7 * ['']
    except subprocess.CalledProcessError:
        output = 7 * ['']
    return {'hash': output[0], 'author': output[1], 'mail': output[2], 'date': output[3], 'message': output[4], 'verified': output[5], 'key': output[6]}


class GitStatus:
    """class for resolving git gpg singing state"""
    class Definition:
        """definition of a git gpg sing state"""
        key: str = 'N'
        status: int = 2
        msg: str = ''

        def __init__(self, key: str = 'N', status: int = 2, msg: str = '') -> None:
            self.key = key
            self.status = status
            self.msg = msg

    N = Definition(key='N', status=2, msg='no signature',)
    G = Definition(key='G', status=0, msg='valid signature',)
    B = Definition(key='B', status=2, msg='bad signature',)
    U = Definition(key='U', status=1, msg='good signature, unknown validity',)
    X = Definition(key='X', status=1, msg='good signature, expired',)
    Y = Definition(key='Y', status=1, msg='good signature, expired key',)
    R = Definition(key='R', status=2, msg='good signature, revoked key',)
    E = Definition(key='E', status=1, msg='cannot be checked',)
# endregion


class IntegrationPlugin(MixinBase, plugin.InvenTreePlugin):
    """
    The IntegrationPlugin class is used to integrate with 3rd party software
    """

    def __init__(self):
        super().__init__()
        self.add_mixin('base')

        self.set_sign_values()

    def mixin(self, key):
        """check if mixin is registered"""
        return key in self._mixins

    def mixin_enabled(self, key):
        """check if mixin is enabled and ready"""
        if self.mixin(key):
            fnc_name = self._mixins.get(key)
            return getattr(self, fnc_name, True)
        return False

    def get_plugin_commit(self):
        """get last git commit for plugin"""
        path = inspect.getfile(self.__class__)
        return get_git_log(path)

    def set_sign_values(self):
        """add the last commit of the plugins class file into plugins context"""
        # fetch git log
        commit = self.get_plugin_commit()
        # resolve state
        sign_state = getattr(GitStatus, commit['verified'], GitStatus.N)

        # set variables
        self.commit = commit
        self.sign_state = sign_state

        if sign_state.status == 0:
            self.sign_color = 'success'
        elif sign_state.status == 1:
            self.sign_color = 'warning'
        else:
            self.sign_color = 'danger'
