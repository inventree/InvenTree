"""Functionality for retrieving metadata about a particular plugin class.

This is performed as external methods, so that plugin classes cannot override functionality.
"""

import datetime
import inspect
import logging
import warnings
from importlib.metadata import PackageNotFoundError, metadata
from pathlib import Path

from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from django.urls import reverse
from django.utils.text import slugify

from InvenTree.config import get_plugin_dir
from plugin.helpers import get_git_log

logger = logging.getLogger('inventree')


def get_plugin_metadata(plugin) -> dict:
    """Extract metadata from the provided plugin class"""

    if not plugin:
        return {}

    try:
        if hasattr(plugin, '__name__'):
            data = metadata(plugin.__name__)
        elif hasattr(plugin, '__class__'):
            data = metadata(plugin.__class__.__name__)
    except PackageNotFoundError:
        data = None
    else:
        data = None

    if data is None:
        try:
            data = metadata(plugin.__module__.split('.')[0])
        except PackageNotFoundError:
            data = None

    # If data not available from metadata, try git logs
    if not data:
        fn = str(get_plugin_file(plugin))
        data = get_git_log(fn)

    # Extract website ifnormation
    try:
        website = data['Project-URL'].split(', ')[1]
    except Exception:
        website = data.get('Project-URL', None)

    # Update date information (if provided)
    date = data.get('Date', data.get('date', None))

    if date:
        date = datetime.datetime.fromisoformat(date)

    return {
        'author': data.get('Author', data.get('Author-email', None)),
        'description': data.get('Summary', data.get('Description', None)),
        'version': data.get('Version', None),
        'website': website,
        'license': data.get('License', None),
        'date': date,
    }


def get_plugin_file(plugin) -> Path:
    """Return the file path of the provided plugin"""

    if plugin is None:
        return None

    path = None

    try:
        path = Path(inspect.getfile(plugin))
    except TypeError:
        pass

    if path is None:
        try:
            path = Path(inspect.getfile(plugin.__class__))
        except TypeError:
            pass

    return path


def get_plugin_path(plugin):
    """Return the installation path of the provided plugin"""

    # Check potential relative paths
    relative_paths = [
        settings.BASE_DIR,
        get_plugin_dir()
    ]

    if plg_file := get_plugin_file(plugin):
        for path in relative_paths:
            try:
                rel_path = plg_file.relative_to(path)
                return rel_path
            except ValueError:
                pass

    if hasattr(plugin, 'is_package'):
        return plugin.__module__

    # Try some backup values if nothing else has worked
    if plg_file is None:
        for attr in ['__module__', '__name__']:
            if hasattr(plugin, attr):
                return getattr(plugin, attr)

    # Finally, return the path
    return plg_file


def get_plugin_pathstring(plugin):
    """Return the plugin path, as a string (or None)"""

    path = get_plugin_path(plugin)

    if path:
        return str(path)
    else:
        return None


def get_plugin_metavalue(plugin, key: str, old_key: str = None, default_value=None):
    """Extract a metadata value from a plugin class

    Arguments:
        plugin: Plugin class
        key: Metadata key
        old_key: Old metadata key (for backwards compatibility)
        default_value: Default value if key is not found
    """
    value = None

    if key and hasattr(plugin, str(key)):
        value = getattr(plugin, str(key), None)

    if value is None and old_key and hasattr(plugin, str(old_key)):
        warnings.warn(f'Usage of {old_key} was deprecated in 0.7.0 in favour of {key}', DeprecationWarning, stacklevel=2)
        value = getattr(plugin, str(old_key), None)

    if value and callable(value):
        # Prevent plugin class from overriding with a callable
        value = None

    if value and isinstance(value, property):
        # Prevent plugin class from overriding with a property
        value = None

    if value is None and default_value is not None:
        value = default_value

    return value


def get_plugin_name(plugin):
    """Return the 'name' of a plugin"""

    return get_plugin_metavalue(plugin, 'NAME', old_key='PLUGIN_NAME')


def get_plugin_slug(plugin):
    """Return the 'slug' of a plugin

    If no slug is found, default to the plugin name (slugified)
    """

    slug = get_plugin_metavalue(plugin, 'SLUG', old_key='PLUGIN_SLUG')

    if not slug:
        slug = get_plugin_name(plugin)

    if slug:
        return slugify(slug.lower())
    else:
        return None


def get_plugin_title(plugin):
    """Return the 'title' of a plugin.

    If no title is found, default to the plugin name
    """

    title = get_plugin_metavalue(plugin, 'TITLE', old_key='PLUGIN_TITLE')

    if not title:
        title = get_plugin_name(plugin)

    return title


def get_plugin_description(plugin):
    """Return the 'description' of a plugin.

    - If no description is explicitly defined, look at plugin metadata
    - If no description is found, default to the plugin name
    """

    description = get_plugin_metavalue(plugin, 'DESCRIPTION', old_key='PLUGIN_DESCRIPTION')

    if not description:
        # Try to extract from package metadata
        description = get_plugin_metadata(plugin).get('description', None)

    if not description:
        description = get_plugin_name(plugin)

    return description


def get_plugin_author(plugin):
    """Return the author of a plugin

    - If no author is explicitly defined, look at plugin metadata
    """

    author = get_plugin_metavalue(plugin, 'AUTHOR')

    if not author:
        author = get_plugin_metadata(plugin).get('author', None)

    return author


def get_plugin_version(plugin):
    """Return the version of a plugin.

    - First, looks for the 'VERSION' attribute
    - If no version is explicitly defined, look at plugin metadata
    """

    version = get_plugin_metavalue(plugin, 'VERSION')

    if not version:
        # Try to extract from package metadata
        version = get_plugin_metadata(plugin).get('version', None)

    return version


def get_plugin_website(plugin):
    """Return the website associated with a plugin

    - If no website is explicitly defined, look at plugin metadata
    """

    website = get_plugin_metavalue(plugin, 'WEBSITE')

    if not website:
        # Try to extract from package metadata
        website = get_plugin_metadata(plugin).get('website', None)

    return website


def get_plugin_license(plugin):
    """Return the license associated with a plugin"""

    license = get_plugin_metavalue(plugin, 'LICENSE')

    if not license:
        # Try to extract from package metadata
        license = get_plugin_metadata(plugin).get('license', None)

    return license


def get_plugin_pubdate(plugin):
    """Return the publish date associated with a plugin"""

    pub_date = get_plugin_metavalue(plugin, 'PUBLISH_DATE')

    if not pub_date:
        # Try to extract from package metadata
        pub_date = get_plugin_metadata(plugin).get('date', None)

    if pub_date:
        pub_date = datetime.datetime.fromisoformat(str(pub_date))

    return pub_date


def get_plugin_config(plugin):
    """Return the PluginConfig object associated with a particular plugin"""

    slug = get_plugin_slug(plugin)
    name = get_plugin_name(plugin)

    try:
        import plugin.models

        if not slug or not name:
            return None

        cfg, _ = plugin.models.PluginConfig.objects.get_or_create(
            key=slug,
            name=name
        )

        return cfg

    except (ImportError, OperationalError, ProgrammingError):
        return None


def get_plugin_settings_url(plugin):
    """Return the settings URL associated with a particular plugin"""

    slug = get_plugin_slug(plugin)

    if slug:
        return reverse('settings') + f'#select-plugin-{slug}'
    else:
        return None
