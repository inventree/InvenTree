# -*- coding: utf-8 -*-
"""class for IntegrationPluginBase and Mixins for it"""

import logging
import os
import subprocess
import inspect
from datetime import datetime
import pathlib

from django.urls.base import reverse
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

import plugin.plugin as plugin


logger = logging.getLogger("inventree")


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
        human_name = getattr(cls.MixinMeta, 'MIXIN_NAME', key) if cls and hasattr(cls, 'MixinMeta') else key

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


class IntegrationPluginBase(MixinBase, plugin.InvenTreePlugin):
    """
    The IntegrationPluginBase class is used to integrate with 3rd party software
    """
    PLUGIN_SLUG = None
    PLUGIN_TITLE = None

    AUTHOR = None
    DESCRIPTION = None
    PUBLISH_DATE = None
    VERSION = None
    WEBSITE = None
    LICENSE = None

    def __init__(self):
        super().__init__()
        self.add_mixin('base')
        self.def_path = inspect.getfile(self.__class__)
        self.path = os.path.dirname(self.def_path)

        self.set_package()

    @property
    def _is_package(self):
        return getattr(self, 'is_package', False)

    # region properties
    @property
    def slug(self):
        """slug for the plugin"""
        slug = getattr(self, 'PLUGIN_SLUG', None)
        if not slug:
            slug = self.plugin_name()
        return slugify(slug)

    @property
    def human_name(self):
        """human readable name for labels etc."""
        human_name = getattr(self, 'PLUGIN_TITLE', None)
        if not human_name:
            human_name = self.plugin_name()
        return human_name

    @property
    def description(self):
        """description of plugin"""
        description = getattr(self, 'DESCRIPTION', None)
        if not description:
            description = self.plugin_name()
        return description

    @property
    def author(self):
        """returns author of plugin - either from plugin settings or git"""
        author = getattr(self, 'AUTHOR', None)
        if not author:
            author = self.package.get('author')
        if not author:
            author = _('No author found')
        return author

    @property
    def pub_date(self):
        """returns publishing date of plugin - either from plugin settings or git"""
        pub_date = getattr(self, 'PUBLISH_DATE', None)
        if not pub_date:
            pub_date = self.package.get('date')
        else:
            pub_date = datetime.fromisoformat(str(pub_date))
        if not pub_date:
            pub_date = _('No date found')
        return pub_date

    @property
    def version(self):
        """returns version of plugin"""
        version = getattr(self, 'VERSION', None)
        return version

    @property
    def website(self):
        """returns website of plugin"""
        website = getattr(self, 'WEBSITE', None)
        return website

    @property
    def license(self):
        """returns license of plugin"""
        license = getattr(self, 'LICENSE', None)
        return license
    # endregion

    @property
    def package_path(self):
        """returns the path to the plugin"""
        if self._is_package:
            return self.__module__
        return pathlib.Path(self.def_path).relative_to(settings.BASE_DIR)

    @property
    def settings_url(self):
        """returns url to the settings panel"""
        return f'{reverse("settings")}#select-plugin-{self.slug}'

    # region mixins
    def mixin(self, key):
        """check if mixin is registered"""
        return key in self._mixins

    def mixin_enabled(self, key):
        """check if mixin is enabled and ready"""
        if self.mixin(key):
            fnc_name = self._mixins.get(key)
            return getattr(self, fnc_name, True)
        return False
    # endregion

    # region package info
    def get_package_commit(self):
        """get last git commit for plugin"""
        return get_git_log(self.def_path)

    def get_package_metadata(self):
        """get package metadata for plugin"""
        return {}

    def set_package(self):
        """add packaging info of the plugins into plugins context"""
        package = self.get_package_metadata() if self._is_package else self.get_package_commit()

        # process date
        if package.get('date'):
            package['date'] = datetime.fromisoformat(package.get('date'))

        # process sign state
        sign_state = getattr(GitStatus, str(package.get('verified')), GitStatus.N)
        if sign_state.status == 0:
            self.sign_color = 'success'
        elif sign_state.status == 1:
            self.sign_color = 'warning'
        else:
            self.sign_color = 'danger'

        # set variables
        self.package = package
        self.sign_state = sign_state
    # endregion
