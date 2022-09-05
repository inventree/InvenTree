"""Base Class for InvenTree plugins."""

import inspect
import logging
import warnings
from datetime import datetime
from distutils.sysconfig import get_python_lib
from importlib.metadata import PackageNotFoundError, metadata
from pathlib import Path

from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from django.urls.base import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from plugin.helpers import GitStatus, get_git_log

logger = logging.getLogger("inventree")


class MetaBase:
    """Base class for a plugins metadata."""

    # Override the plugin name for each concrete plugin instance
    NAME = ''
    SLUG = None
    TITLE = None

    def get_meta_value(self, key: str, old_key: str = None, __default=None):
        """Reference a meta item with a key.

        Args:
            key (str): key for the value
            old_key (str, optional): depreceated key - will throw warning
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
                warnings.warn(f'Usage of {old_key} was depreciated in 0.7.0 in favour of {key}', DeprecationWarning)

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
        try:
            import plugin.models

            cfg, _ = plugin.models.PluginConfig.objects.get_or_create(
                key=self.plugin_slug(),
                name=self.plugin_name(),
            )
        except (OperationalError, ProgrammingError):
            cfg = None

        return cfg

    def is_active(self):
        """Return True if this plugin is currently active."""
        cfg = self.plugin_config()

        if cfg:
            return cfg.active
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
        }

    @property
    def registered_mixins(self, with_base: bool = False):
        """Get all registered mixins for the plugin."""
        mixins = getattr(self, '_mixinreg', None)
        if mixins:
            # filter out base
            if not with_base and 'base' in mixins:
                del mixins['base']
            # only return dict
            mixins = [a for a in mixins.values()]
        return mixins


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

        self.define_package()

    @classmethod
    def file(cls) -> Path:
        """File that contains plugin definition."""
        return Path(inspect.getfile(cls))

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
        if not pub_date:
            pub_date = _('No date found')  # pragma: no cover
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

    @property
    def settings_url(self):
        """URL to the settings panel for this plugin."""
        return f'{reverse("settings")}#select-plugin-{self.slug}'

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
        # Simpel lookup did not work - get data from module
        except PackageNotFoundError:
            meta = metadata(cls.__module__.split('.')[0])

        return {
            'author': meta['Author-email'],
            'description': meta['Summary'],
            'version': meta['Version'],
            'website': meta['Project-URL'],
            'license': meta['License']
        }

    def define_package(self):
        """Add package info of the plugin into plugins context."""
        package = self._get_package_metadata() if self._is_package else self._get_package_commit()

        # process date
        if package.get('date'):
            package['date'] = datetime.fromisoformat(package.get('date'))

        # process sign state
        sign_state = getattr(GitStatus, str(package.get('verified')), GitStatus.N)
        if sign_state.status == 0:
            self.sign_color = 'success'  # pragma: no cover
        elif sign_state.status == 1:
            self.sign_color = 'warning'
        else:
            self.sign_color = 'danger'  # pragma: no cover

        # set variables
        self.package = package
        self.sign_state = sign_state
    # endregion
