"""Base Class for InvenTree plugins."""

import inspect
import warnings
from datetime import datetime
from distutils.sysconfig import get_python_lib
from importlib.metadata import PackageNotFoundError, metadata
from pathlib import Path
from typing import Optional

from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

import structlog

import InvenTree.helpers
from plugin.helpers import get_git_log

logger = structlog.get_logger('inventree')


class MetaBase:
    """Base class for a plugins metadata."""

    # Override the plugin name for each concrete plugin instance
    NAME = ''
    SLUG = None
    TITLE = None

    def get_meta_value(self, key: str, old_key: Optional[str] = None, __default=None):
        """Reference a meta item with a key.

        Args:
            key (str): key for the value
            old_key (str, optional): deprecated key - will throw warning
            __default (optional): Value if nothing with key can be found. Defaults to None.

        Returns:
            Value referenced with key, old_key or __default if set and not value found
        """
        value = getattr(self, key, None)

        # The key was not used
        if old_key and value is None:
            value = getattr(self, old_key, None)

            # Sound of a warning if old_key worked
            if value:
                warnings.warn(
                    f'Usage of {old_key} was depreciated in 0.7.0 in favour of {key}',
                    DeprecationWarning,
                    stacklevel=2,
                )

        # Use __default if still nothing set
        if (value is None) and __default:
            return __default
        return value

    def plugin_name(self):
        """Name of plugin."""
        return self.get_meta_value('NAME', 'PLUGIN_NAME')

    @property
    def name(self):
        """Name of plugin."""
        return self.plugin_name()

    def plugin_slug(self):
        """Slug of plugin.

        If not set plugin name slugified
        """
        slug = self.get_meta_value('SLUG', 'PLUGIN_SLUG', None)
        if not slug:
            slug = self.plugin_name()

        return slugify(slug.lower())

    @property
    def slug(self):
        """Slug of plugin."""
        return self.plugin_slug()

    def plugin_title(self):
        """Title of plugin."""
        title = self.get_meta_value('TITLE', 'PLUGIN_TITLE', None)
        if title:
            return title
        return self.plugin_name()

    @property
    def human_name(self):
        """Human readable name of plugin."""
        return self.plugin_title()

    def plugin_config(self):
        """Return the PluginConfig object associated with this plugin."""
        from plugin.registry import registry

        return registry.get_plugin_config(self.plugin_slug())

    def is_active(self):
        """Return True if this plugin is currently active."""
        # Builtin plugins are always considered "active"
        if self.is_builtin:
            return True

        config = self.plugin_config()

        if config:
            return config.active
        return False  # pragma: no cover


class MixinBase:
    """Base set of mixin functions and mechanisms."""

    def __init__(self, *args, **kwargs) -> None:
        """Init sup-parts.

        Adds state dicts.
        """
        self._mixinreg = {}
        self._mixins = {}
        super().__init__(*args, **kwargs)

    def mixin(self, key):
        """Check if mixin is registered."""
        return key in self._mixins

    def mixin_enabled(self, key):
        """Check if mixin is registered, enabled and ready."""
        if self.mixin(key):
            fnc_name = self._mixins.get(key)

            # Allow for simple case where the mixin is "always" ready
            if fnc_name is True:
                return True

            attr = getattr(self, fnc_name, True)

            if callable(attr):
                return attr()
            else:
                return attr

        return False

    def add_mixin(self, key: str, fnc_enabled=True, cls=None):
        """Add a mixin to the plugins registry."""
        self._mixins[key] = fnc_enabled
        self.setup_mixin(key, cls=cls)

    def setup_mixin(self, key, cls=None):
        """Define mixin details for the current mixin -> provides meta details for all active mixins."""
        # get human name
        human_name = (
            getattr(cls.MixinMeta, 'MIXIN_NAME', key)
            if cls and hasattr(cls, 'MixinMeta')
            else key
        )

        # register
        self._mixinreg[key] = {'key': key, 'human_name': human_name, 'cls': cls}

    def get_registered_mixins(self, with_base: bool = False, with_cls: bool = True):
        """Get all registered mixins for the plugin."""
        mixins = getattr(self, '_mixinreg', None)
        if not mixins:
            return {}

        mixins = mixins.copy()
        # filter out base
        if not with_base and 'base' in mixins:
            del mixins['base']

        # Do not return the mixin class if flas is set
        if not with_cls:
            return {
                key: {k: v for k, v in mixin.items() if k != 'cls'}
                for key, mixin in mixins.items()
            }
        return mixins

    @property
    def registered_mixins(self, with_base: bool = False):
        """Get all registered mixins for the plugin."""
        return self.get_registered_mixins(with_base=with_base)


class VersionMixin:
    """Mixin to enable version checking."""

    MIN_VERSION = None
    MAX_VERSION = None

    def check_version(self, latest=None) -> bool:
        """Check if plugin functions for the current InvenTree version."""
        from InvenTree import version

        latest = latest if latest else version.inventreeVersionTuple()
        min_v = version.inventreeVersionTuple(self.MIN_VERSION)
        max_v = version.inventreeVersionTuple(self.MAX_VERSION)

        return bool(min_v <= latest <= max_v)


class InvenTreePlugin(VersionMixin, MixinBase, MetaBase):
    """The InvenTreePlugin class is used to integrate with 3rd party software.

    DO NOT USE THIS DIRECTLY, USE plugin.InvenTreePlugin
    """

    AUTHOR = None
    DESCRIPTION = None
    PUBLISH_DATE = None
    VERSION = None
    WEBSITE = None
    LICENSE = None

    # Optional path to a JavaScript file which will be loaded in the admin panel
    # This file must provide a function called renderPluginSettings
    ADMIN_SOURCE = None

    def __init__(self):
        """Init a plugin.

        Set paths and load metadata.
        """
        super().__init__()
        self.add_mixin('base')

        self.define_package()

    @classmethod
    def file(cls) -> Path:
        """File that contains plugin definition."""
        return Path(inspect.getfile(cls))

    @classmethod
    def path(cls) -> Path:
        """Path to plugins base folder."""
        return cls.file().parent

    def _get_value(self, meta_name: str, package_name: str) -> str:
        """Extract values from class meta or package info.

        Args:
            meta_name (str): Name of the class meta to use.
            package_name (str): Name of the package data to use.

        Returns:
            str: Extracted value, None if nothing found.
        """
        val = getattr(self, meta_name, None)
        if not val:
            val = self.package.get(package_name, None)
        return val

    # region properties
    @property
    def description(self):
        """Description of plugin."""
        description = self._get_value('DESCRIPTION', 'description')
        if not description:
            description = self.plugin_name()
        return description

    @property
    def author(self):
        """Author of plugin - either from plugin settings or git."""
        author = self._get_value('AUTHOR', 'author')
        if not author:
            author = _('No author found')  # pragma: no cover
        return author

    @property
    def pub_date(self):
        """Publishing date of plugin - either from plugin settings or git."""
        pub_date = getattr(self, 'PUBLISH_DATE', None)
        if not pub_date:
            pub_date = self.package.get('date')
        else:
            pub_date = datetime.fromisoformat(str(pub_date))

        return pub_date

    @property
    def version(self):
        """Version of plugin."""
        return self._get_value('VERSION', 'version')

    @property
    def website(self):
        """Website of plugin - if set else None."""
        return self._get_value('WEBSITE', 'website')

    @property
    def license(self):
        """License of plugin."""
        return self._get_value('LICENSE', 'license')

    # endregion

    @classmethod
    def check_is_package(cls):
        """Is the plugin delivered as a package."""
        return getattr(cls, 'is_package', False)

    @property
    def _is_package(self):
        """Is the plugin delivered as a package."""
        return getattr(self, 'is_package', False)

    @classmethod
    def check_is_sample(cls) -> bool:
        """Is this plugin part of the samples?"""
        return str(cls.check_package_path()).startswith('plugin/samples/')

    @property
    def is_sample(self) -> bool:
        """Is this plugin part of the samples?"""
        return self.check_is_sample()

    @classmethod
    def check_is_builtin(cls) -> bool:
        """Determine if a particular plugin class is a 'builtin' plugin."""
        return str(cls.check_package_path()).startswith('plugin/builtin')

    @property
    def is_builtin(self) -> bool:
        """Is this plugin is builtin."""
        return self.check_is_builtin()

    @classmethod
    def check_package_path(cls):
        """Path to the plugin."""
        if cls.check_is_package():
            return cls.__module__  # pragma: no cover

        try:
            return cls.file().relative_to(settings.BASE_DIR)
        except ValueError:
            return cls.file()

    @property
    def package_path(self):
        """Path to the plugin."""
        return self.check_package_path()

    @classmethod
    def check_package_install_name(cls) -> [str, None]:
        """Installable package name of the plugin.

        e.g. if this plugin was installed via 'pip install <x>',
        then this function should return '<x>'

        Returns:
            str: Install name of the package, else None
        """
        return getattr(cls, 'package_name', None)

    @property
    def package_install_name(self) -> [str, None]:
        """Installable package name of the plugin.

        e.g. if this plugin was installed via 'pip install <x>',
        then this function should return '<x>'

        Returns:
            str: Install name of the package, else None
        """
        return self.check_package_install_name()

    @property
    def settings_url(self) -> str:
        """URL to the settings panel for this plugin."""
        if config := self.db:
            return InvenTree.helpers.pui_url(f'/settings/admin/plugin/{config.pk}/')
        return InvenTree.helpers.pui_url('/settings/admin/plugin/')

    # region package info
    def _get_package_commit(self):
        """Get last git commit for the plugin."""
        return get_git_log(str(self.file()))

    @classmethod
    def is_editable(cls):
        """Returns if the current part is editable."""
        pkg_name = cls.__name__.split('.')[0]
        dist_info = list(Path(get_python_lib()).glob(f'{pkg_name}-*.dist-info'))
        return bool(len(dist_info) == 1)

    @classmethod
    def _get_package_metadata(cls):
        """Get package metadata for plugin."""
        # Try simple metadata lookup
        try:
            meta = metadata(cls.__name__)
        # Simple lookup did not work - get data from module
        except PackageNotFoundError:
            try:
                meta = metadata(cls.__module__.split('.')[0])
            except PackageNotFoundError:
                # Not much information we can extract at this point
                return {}

        try:
            website = meta['Project-URL'].split(', ')[1]
        except (ValueError, IndexError, AttributeError):
            website = meta['Project-URL']

        return {
            'author': meta['Author-email'],
            'description': meta['Summary'],
            'version': meta['Version'],
            'website': website,
            'license': meta['License'],
        }

    def define_package(self):
        """Add package info of the plugin into plugins context."""
        try:
            package = (
                self._get_package_metadata()
                if self._is_package
                else self._get_package_commit()
            )
        except TypeError:
            package = {}

        # process date
        if package.get('date'):
            package['date'] = datetime.fromisoformat(package.get('date'))

        # set variables
        self.package = package

    # endregion

    def plugin_static_file(self, *args):
        """Construct a path to a static file within the plugin directory."""
        import os

        from django.conf import settings

        url = os.path.join(settings.STATIC_URL, 'plugins', self.SLUG, *args)

        if not url.startswith('/'):
            url = '/' + url

        return url

    def get_admin_source(self) -> str:
        """Return a path to a JavaScript file which contains custom UI settings.

        The frontend code expects that this file provides a function named 'renderPluginSettings'.
        """
        if not self.ADMIN_SOURCE:
            return None

        return self.plugin_static_file(self.ADMIN_SOURCE)

    def get_admin_context(self) -> dict:
        """Return a context dictionary for the admin panel settings.

        This is an optional method which can be overridden by the plugin.
        """
        return None
