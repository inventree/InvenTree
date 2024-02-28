"""Helper functions for loading InvenTree configuration options."""

import datetime
import json
import logging
import os
import random
import shutil
import string
import warnings
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import Storage

logger = logging.getLogger('inventree')
CONFIG_DATA = None
CONFIG_LOOKUPS = {}


def to_list(value, delimiter=','):
    """Take a configuration setting and make sure it is a list.

    For example, we might have a configuration setting taken from the .config file,
    which is already a list.

    However, the same setting may be specified via an environment variable,
    using a comma delimited string!
    """
    if type(value) in [list, tuple]:
        return value

    # Otherwise, force string value
    value = str(value)

    return [x.strip() for x in value.split(delimiter)]


def to_dict(value):
    """Take a configuration setting and make sure it is a dict.

    For example, we might have a configuration setting taken from the .config file,
    which is already an object/dict.

    However, the same setting may be specified via an environment variable,
    using a valid JSON string!
    """
    if value is None:
        return {}

    if isinstance(value, dict):
        return value

    try:
        return json.loads(value)
    except Exception as error:
        logger.exception(
            "Failed to parse value '%s' as JSON with error %s. Ensure value is a valid JSON string.",
            value,
            error,
        )
    return {}


def is_true(x):
    """Shortcut function to determine if a value "looks" like a boolean."""
    return str(x).strip().lower() in ['1', 'y', 'yes', 't', 'true', 'on']


def get_base_dir() -> Path:
    """Returns the base (top-level) InvenTree directory."""
    return Path(__file__).parent.parent.resolve()


def ensure_dir(path: Path, storage=None) -> None:
    """Ensure that a directory exists.

    If it does not exist, create it.
    """
    if storage and isinstance(storage, Storage):
        if not storage.exists(str(path)):
            storage.save(str(path / '.empty'), ContentFile(''))
        return

    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


def get_config_file(create=True) -> Path:
    """Returns the path of the InvenTree configuration file.

    Note: It will be created it if does not already exist!

    Operation order:
    - INVENTREE_CONFIG_FILE environment variable
    - Old default location (if it exists)
    - Default location (create if it does not exist)
    """
    cfg_filename = os.getenv('INVENTREE_CONFIG_FILE')

    if cfg_filename:
        cfg_filename = Path(cfg_filename.strip()).resolve()
    elif get_path('config.yaml', old=True).exists():
        # Config file is *not* specified - see if the old default exists
        cfg_filename = get_path('config.yaml', old=True)
    else:
        # Config file is *not* specified - use the default
        cfg_filename = get_path('config.yaml')

    if not cfg_filename.exists() and create:
        print(
            "InvenTree configuration file 'config.yaml' not found - creating default file"
        )
        ensure_dir(cfg_filename.parent)

        cfg_template = get_path('config_template.yaml')
        shutil.copyfile(cfg_template, cfg_filename)
        print(f'Created config file {cfg_filename}')

    return cfg_filename


def load_config_data(set_cache: bool = False) -> map:
    """Load configuration data from the config file.

    Arguments:
        set_cache(bool): If True, the configuration data will be cached for future use after load.
    """
    global CONFIG_DATA

    # use cache if populated
    # skip cache if cache should be set
    if CONFIG_DATA is not None and not set_cache:
        return CONFIG_DATA

    import yaml

    cfg_file = get_config_file()

    with open(cfg_file, 'r') as cfg:
        data = yaml.safe_load(cfg)

    # Set the cache if requested
    if set_cache:
        CONFIG_DATA = data

    return data


def do_typecast(value, type, var_name=None):
    """Attempt to typecast a value.

    Arguments:
        value: Value to typecast
        type: Function to use for typecasting the value e.g. int, float, str, list, dict
        var_name: Name that should be logged e.g. 'INVENTREE_STATIC_ROOT'. Set if logging is required.

    Returns:
        Typecasted value or original value if typecasting failed.
    """
    # Force 'list' of strings
    if type is list:
        value = to_list(value)

    # Valid JSON string is required
    elif type is dict:
        value = to_dict(value)

    elif type is not None:
        # Try to typecast the value
        try:
            val = type(value)
            return val
        except Exception as error:
            if var_name:
                logger.exception(
                    "Failed to typecast '%s' with value '%s' to type '%s' with error %s",
                    var_name,
                    value,
                    type,
                    error,
                )
    return value


def get_setting(env_var=None, config_key=None, default_value=None, typecast=None):
    """Helper function for retrieving a configuration setting value.

    - First preference is to look for the environment variable
    - Second preference is to look for the value of the settings file
    - Third preference is the default value

    Arguments:
        env_var: Name of the environment variable e.g. 'INVENTREE_STATIC_ROOT'
        config_key: Key to lookup in the configuration file
        default_value: Value to return if first two options are not provided
        typecast: Function to use for typecasting the value e.g. int, float, str, list, dict
    """

    def set_metadata(source: str):
        """Set lookup metadata for the setting."""
        key = env_var or config_key
        CONFIG_LOOKUPS[key] = {
            'env_var': env_var,
            'config_key': config_key,
            'source': source,
            'accessed': datetime.datetime.now(),
        }

    # First, try to load from the environment variables
    if env_var is not None:
        val = os.getenv(env_var, None)

        if val is not None:
            set_metadata('env')
            return do_typecast(val, typecast, var_name=env_var)

    # Next, try to load from configuration file
    if config_key is not None:
        cfg_data = load_config_data()

        result = None

        # Hack to allow 'path traversal' in configuration file
        for key in config_key.strip().split('.'):
            if type(cfg_data) is not dict or key not in cfg_data:
                result = None
                break

            result = cfg_data[key]
            cfg_data = cfg_data[key]

        if result is not None:
            set_metadata('yaml')
            return do_typecast(result, typecast, var_name=env_var)

    # Finally, return the default value
    set_metadata('default')
    return do_typecast(default_value, typecast, var_name=env_var)


def get_boolean_setting(env_var=None, config_key=None, default_value=False):
    """Helper function for retrieving a boolean configuration setting."""
    return is_true(get_setting(env_var, config_key, default_value))


def get_media_dir(create=True):
    """Return the absolute path for the 'media' directory (where uploaded files are stored)."""
    md = get_setting('INVENTREE_MEDIA_ROOT', 'media_root')

    if not md:
        raise FileNotFoundError('INVENTREE_MEDIA_ROOT not specified')

    md = Path(md).resolve()

    if create:
        md.mkdir(parents=True, exist_ok=True)

    return md


def get_static_dir(create=True):
    """Return the absolute path for the 'static' directory (where static files are stored)."""
    sd = get_setting('INVENTREE_STATIC_ROOT', 'static_root')

    if not sd:
        raise FileNotFoundError('INVENTREE_STATIC_ROOT not specified')

    sd = Path(sd).resolve()

    if create:
        sd.mkdir(parents=True, exist_ok=True)

    return sd


def get_backup_dir(create=True):
    """Return the absolute path for the backup directory."""
    bd = get_setting('INVENTREE_BACKUP_DIR', 'backup_dir')

    if not bd:
        raise FileNotFoundError('INVENTREE_BACKUP_DIR not specified')

    bd = Path(bd).resolve()

    if create:
        bd.mkdir(parents=True, exist_ok=True)

    return bd


def get_plugin_file():
    """Returns the path of the InvenTree plugins specification file.

    Note: It will be created if it does not already exist!
    """
    # Check if the plugin.txt file (specifying required plugins) is specified
    plugin_file_cfg = get_setting('INVENTREE_PLUGIN_FILE', 'plugin_file')

    if plugin_file_cfg and isinstance(plugin_file_cfg, str):
        # Make sure we are using a modern Path object
        plugin_file = Path(plugin_file_cfg).resolve()
    elif get_path('plugins.txt', old=True).exists():
        # See if the old default exists
        plugin_file = get_path('plugins.txt', old=True)
    else:
        # Use the default
        plugin_file = get_config_file().joinpath('..', 'plugins.txt').resolve()

    if not plugin_file.exists():
        logger.warning(
            'Plugin configuration file does not exist - creating default file'
        )
        logger.info("Creating plugin file at '%s'", plugin_file)
        ensure_dir(plugin_file.parent)

        # If opening the file fails (no write permission, for example), then this will throw an error
        plugin_file.write_text(
            '# InvenTree Plugins (uses PIP framework to install)\n\n'
        )

    return plugin_file


def get_plugin_dir():
    """Returns the path of the custom plugins directory."""
    return get_setting('INVENTREE_PLUGIN_DIR', 'plugin_dir')


def get_secret_key():
    """Return the secret key value which will be used by django.

    Following options are tested, in descending order of preference:

    A) Check for environment variable INVENTREE_SECRET_KEY => Use raw key data
    B) Check for environment variable INVENTREE_SECRET_KEY_FILE => Load key data from file
    C) Look for old default key file
    D) Look for default key file "secret_key.txt"
    E) Create "secret_key.txt" if it does not exist
    """
    # Look for environment variable
    if secret_key := get_setting('INVENTREE_SECRET_KEY', 'secret_key'):
        logger.info('SECRET_KEY loaded by INVENTREE_SECRET_KEY')  # pragma: no cover
        return secret_key

    # Look for secret key file
    if secret_key_file := get_setting('INVENTREE_SECRET_KEY_FILE', 'secret_key_file'):
        secret_key_file = Path(secret_key_file).resolve()
    elif get_path('secret_key.txt', old=True).exists():
        # Old default location for secret key file
        secret_key_file = get_path('secret_key.txt', old=True)
    else:
        # Default location for secret key file
        secret_key_file = get_path('secret_key.txt')

    if not secret_key_file.exists():
        logger.info("Generating random key file at '%s'", secret_key_file)
        ensure_dir(secret_key_file.parent)

        # Create a random key file
        options = string.digits + string.ascii_letters + string.punctuation
        key = ''.join([random.choice(options) for i in range(100)])
        secret_key_file.write_text(key)

    logger.debug("Loading SECRET_KEY from '%s'", secret_key_file)

    key_data = secret_key_file.read_text().strip()

    return key_data


def get_custom_file(
    env_ref: str, conf_ref: str, log_ref: str, lookup_media: bool = False
):
    """Returns the checked path to a custom file.

    Set lookup_media to True to also search in the media folder.
    """
    from django.contrib.staticfiles.storage import StaticFilesStorage
    from django.core.files.storage import default_storage

    value = get_setting(env_ref, conf_ref, None)

    if not value:
        return None

    static_storage = StaticFilesStorage()

    if static_storage.exists(value):
        logger.info('Loading %s from %s directory: %s', log_ref, 'static', value)
    elif lookup_media and default_storage.exists(value):
        logger.info('Loading %s from %s directory: %s', log_ref, 'media', value)
    else:
        add_dir_str = ' or media' if lookup_media else ''
        logger.warning(
            "The %s file '%s' could not be found in the static %s directories",
            log_ref,
            value,
            add_dir_str,
        )
        value = False

    return value


def get_frontend_settings(debug=True):
    """Return a dictionary of settings for the frontend interface.

    Note that the new config settings use the 'FRONTEND' key,
    whereas the legacy key was 'PUI' (platform UI) which is now deprecated
    """
    # Legacy settings
    pui_settings = get_setting(
        'INVENTREE_PUI_SETTINGS', 'pui_settings', {}, typecast=dict
    )

    if len(pui_settings) > 0:
        warnings.warn(
            "The 'INVENTREE_PUI_SETTINGS' key is deprecated. Please use 'INVENTREE_FRONTEND_SETTINGS' instead",
            DeprecationWarning,
            stacklevel=2,
        )

    # New settings
    frontend_settings = get_setting(
        'INVENTREE_FRONTEND_SETTINGS', 'frontend_settings', {}, typecast=dict
    )

    # Merge settings
    settings = {**pui_settings, **frontend_settings}

    # Set the base URL
    if 'base_url' not in settings:
        base_url = get_setting('INVENTREE_PUI_URL_BASE', 'pui_url_base', '')

        if base_url:
            warnings.warn(
                "The 'INVENTREE_PUI_URL_BASE' key is deprecated. Please use 'INVENTREE_FRONTEND_URL_BASE' instead",
                DeprecationWarning,
                stacklevel=2,
            )
        else:
            base_url = get_setting(
                'INVENTREE_FRONTEND_URL_BASE', 'frontend_url_base', 'platform'
            )

        settings['base_url'] = base_url

    # Set the server list
    settings['server_list'] = settings.get('server_list', [])

    # Set the debug flag
    settings['debug'] = debug

    if 'environment' not in settings:
        settings['environment'] = 'development' if debug else 'production'

    if debug and 'show_server_selector' not in settings:
        # In debug mode, show server selector by default
        settings['show_server_selector'] = True
    elif len(settings['server_list']) == 0:
        # If no servers are specified, show server selector
        settings['show_server_selector'] = True

    return settings
