"""Helper functions for loading InvenTree configuration options."""

import logging
import os
import random
import shutil
import string
from pathlib import Path

import yaml

logger = logging.getLogger('inventree')


def is_true(x):
    """Shortcut function to determine if a value "looks" like a boolean"""
    return str(x).strip().lower() in ['1', 'y', 'yes', 't', 'true', 'on']


def get_base_dir() -> Path:
    """Returns the base (top-level) InvenTree directory."""
    return Path(__file__).parent.parent.resolve()


def get_config_file(create=True) -> Path:
    """Returns the path of the InvenTree configuration file.

    Note: It will be created it if does not already exist!
    """
    base_dir = get_base_dir()

    cfg_filename = os.getenv('INVENTREE_CONFIG_FILE')

    if cfg_filename:
        cfg_filename = Path(cfg_filename.strip()).resolve()
    else:
        # Config file is *not* specified - use the default
        cfg_filename = base_dir.joinpath('config.yaml').resolve()

    if not cfg_filename.exists() and create:
        print("InvenTree configuration file 'config.yaml' not found - creating default file")

        cfg_template = base_dir.joinpath("config_template.yaml")
        shutil.copyfile(cfg_template, cfg_filename)
        print(f"Created config file {cfg_filename}")

    return cfg_filename


def load_config_data() -> map:
    """Load configuration data from the config file."""

    cfg_file = get_config_file()

    with open(cfg_file, 'r') as cfg:
        data = yaml.safe_load(cfg)

    return data


def get_secret_key():
    """Return the secret key value which will be used by django.

    Following options are tested, in descending order of preference:

    A) Check for environment variable INVENTREE_SECRET_KEY => Use raw key data
    B) Check for environment variable INVENTREE_SECRET_KEY_FILE => Load key data from file
    C) Look for default key file "secret_key.txt"
    D) Create "secret_key.txt" if it does not exist
    """

    # Look for environment variable
    if secret_key := os.getenv('INVENTREE_SECRET_KEY'):
        logger.info("SECRET_KEY loaded by INVENTREE_SECRET_KEY")  # pragma: no cover
        return secret_key

    # Look for secret key file
    if secret_key_file := os.getenv('INVENTREE_SECRET_KEY_FILE'):
        secret_key_file = Path(secret_key_file).resolve()
    else:
        # Default location for secret key file
        secret_key_file = get_base_dir().joinpath("secret_key.txt").resolve()

    if not secret_key_file.exists():
        logger.info(f"Generating random key file at '{secret_key_file}'")

        # Create a random key file
        options = string.digits + string.ascii_letters + string.punctuation
        key = ''.join([random.choice(options) for i in range(100)])
        secret_key_file.write_text(key)

    logger.info(f"Loading SECRET_KEY from '{secret_key_file}'")

    with open(secret_key_file, 'r') as f:
        key_data = f.read().strip()

    return key_data


def get_setting(env_var=None, config_key=None, default_value=None):
    """Helper function for retrieving a configuration setting value.

    - First preference is to look for the environment variable
    - Second preference is to look for the value of the settings file
    - Third preference is the default value

    Arguments:
        env_var: Name of the environment variable e.g. 'INVENTREE_STATIC_ROOT'
        config_key: Key to lookup in the configuration file
        default_value: Value to return if first two options are not provided

    """

    # First, try to load from the environment variables
    if env_var is not None:
        val = os.getenv(env_var, None)

        if val is not None:
            return val

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
            return result

    # Finally, return the default value
    return default_value


def get_boolean_setting(env_var=None, config_key=None, default_value=False):
    """Helper function for retreiving a boolean configuration setting"""

    return is_true(get_setting(env_var, config_key, default_value))


def get_media_dir(create=True):
    """Return the absolute path for the 'media' directory (where uploaded files are stored)"""

    md = get_setting('INVENTREE_MEDIA_ROOT', 'media_root')

    if not md:
        raise FileNotFoundError('INVENTREE_MEDIA_ROOT not specified')

    md = Path(md)

    if create:
        md.mkdir(parents=True, exist_ok=True)

    return md


def get_static_dir(cfg_data=None, create=True):
    """Return the absolute path for the 'static' directory (where static files are stored)"""

    if not cfg_data:
        cfg_data = load_config_data()

    sd = get_setting('INVENTREE_STATIC_ROOT', 'static_root')

    if not sd:
        raise FileNotFoundError('INVENTREE_STATIC_ROOT not specified')

    sd = Path(sd)

    if create:
        sd.mkdir(parents=True, exist_ok=True)

    return sd


def get_plugin_file():
    """Returns the path of the InvenTree plugins specification file.

    Note: It will be created if it does not already exist!
    """

    # Check if the plugin.txt file (specifying required plugins) is specified
    plugin_file = get_setting('INVENTREE_PLUGIN_FILE', 'plugins.plugin_file')

    if not plugin_file:
        # If not specified, look in the same directory as the configuration file
        config_dir = get_config_file().parent
        plugin_file = config_dir.joinpath('plugins.txt')
    else:
        # Make sure we are using a modern Path object
        plugin_file = Path(plugin_file)

    if not plugin_file.exists():
        logger.warning("Plugin configuration file does not exist - creating default file")
        logger.info(f"Creating plugin file at '{plugin_file}'")

        # If opening the file fails (no write permission, for example), then this will throw an error
        plugin_file.write_text("# InvenTree Plugins (uses PIP framework to install)\n\n")

    return plugin_file
