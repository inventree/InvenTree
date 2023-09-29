"""Base Class for InvenTree plugins."""

import logging
from distutils.sysconfig import get_python_lib
from pathlib import Path

import plugin.meta

logger = logging.getLogger("inventree")


class MetaBase:
    """Base class for a plugins metadata."""

    # Override the plugin name for each concrete plugin instance
    NAME = ''
    SLUG = None
    TITLE = None

    def plugin_name(self):
        """Name of plugin."""
        return plugin.meta.get_plugin_name(self)

    @property
    def name(self):
        """Name of plugin."""
        return self.plugin_name()

    def plugin_slug(self):
        """Return the slug associated with this plugin class"""
        return plugin.meta.get_plugin_slug(self)

    @property
    def slug(self):
        """Slug of plugin."""
        return self.plugin_slug()

    def plugin_title(self):
        """Return the title associated with this plugin class"""
        return plugin.meta.get_plugin_title(self)

    @property
    def human_name(self):
        """Human readable name of plugin."""
        return self.plugin_title()

    def plugin_config(self):
        """Return the PluginConfig object associated with this plugin."""
        return plugin.meta.get_plugin_config(self)

    def is_active(self):
        """Return True if this plugin is currently active."""

        # Builtin plugins are always considered "active"
        if self.is_builtin:
            return True

        config = self.plugin_config()

        if config:
            return config.active
        else:
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

    @classmethod
    def inherits_mixin(cls, mixin_class):
        """Check if a particular mixin is inherited by this class.

        This check is separate to the following 'mixin_enabled' method,
        as it is class method which can be called without instantiating the plugin.
        """
        return issubclass(cls, mixin_class)

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

            return getattr(self, fnc_name, True)
        return False

    def add_mixin(self, key: str, fnc_enabled=True, cls=None):
        """Add a mixin to the plugins registry."""
        self._mixins[key] = fnc_enabled
        self.setup_mixin(key, cls=cls)

    def setup_mixin(self, key, cls=None):
        """Define mixin details for the current mixin -> provides meta details for all active mixins."""
        # get human name
        human_name = getattr(cls.MixinMeta, 'MIXIN_NAME', key) if cls and hasattr(cls, 'MixinMeta') else key

        # register
        self._mixinreg[key] = {
            'key': key,
            'human_name': human_name,
            'cls': cls,
        }

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
            return {key: {k: v for k, v in mixin.items() if k != 'cls'} for key, mixin in mixins.items()}
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

    def __init__(self):
        """Init a plugin.

        Set paths and load metadata.
        """
        super().__init__()
        self.add_mixin('base')

        self.package = self._get_package_metadata()

    @classmethod
    def file(cls) -> Path:
        """File that contains plugin definition."""
        return plugin.meta.get_plugin_file(cls)

    def path(self) -> Path:
        """Path to plugins base folder."""
        return self.file().parent

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

    @property
    def description(self):
        """Description of plugin."""
        return plugin.meta.get_plugin_description(self)

    @property
    def author(self):
        """Author of plugin - either from plugin settings or git."""
        return plugin.meta.get_plugin_author(self)

    @property
    def pub_date(self):
        """Publishing date of plugin - either from plugin settings or git."""
        return plugin.meta.get_plugin_pubdate(self)

    @property
    def version(self):
        """Version of plugin."""
        return plugin.meta.get_plugin_version(self)

    @property
    def website(self):
        """Website of plugin - if set else None."""
        return plugin.meta.get_plugin_website(self)

    @property
    def license(self):
        """License of plugin."""
        return plugin.meta.get_plugin_license(self)

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
        """Determine if a particular plugin class is a 'builtin' plugin"""
        return str(cls.check_package_path()).startswith('plugin/builtin')

    @property
    def is_builtin(self) -> bool:
        """Is this plugin is builtin"""
        return self.check_is_builtin()

    @classmethod
    def check_package_path(cls):
        """Path to the plugin."""

        return plugin.meta.get_plugin_path(cls)

    @property
    def package_path(self):
        """Path to the plugin."""
        return self.check_package_path()

    @property
    def settings_url(self):
        """URL to the settings panel for this plugin."""
        return plugin.meta.get_plugin_settings_url(self)

    @classmethod
    def is_editable(cls):
        """Returns if the current part is editable."""
        pkg_name = cls.__name__.split('.')[0]
        dist_info = list(Path(get_python_lib()).glob(f'{pkg_name}-*.dist-info'))
        return bool(len(dist_info) == 1)

    @classmethod
    def _get_package_metadata(cls):
        """Get package metadata for plugin."""

        return plugin.meta.get_plugin_metadata(cls)
