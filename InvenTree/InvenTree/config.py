"""Helper functions for loading InvenTree configuration options."""

import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger('inventree')


def get_base_dir() -> Path:
    """Returns the base (top-level) InvenTree directory."""
    return Path(__file__).parent.parent.absolute()


def get_config_file() -> Path:
    """Returns the path of the InvenTree configuration file.

    Note: It will be created it if does not already exist!
    """
    base_dir = get_base_dir()

    cfg_filename = os.getenv('INVENTREE_CONFIG_FILE')

    if cfg_filename:
        cfg_filename = Path(cfg_filename.strip())
    else:
        # Config file is *not* specified - use the default
        cfg_filename = base_dir.joinpath('config.yaml')

    if not cfg_filename.exists():
        print("InvenTree configuration file 'config.yaml' not found - creating default file")

        cfg_template = base_dir.joinpath("config_template.yaml")
        shutil.copyfile(cfg_template, cfg_filename)
        print(f"Created config file {cfg_filename}")

    return cfg_filename


def get_plugin_file():
    """Returns the path of the InvenTree plugins specification file.

    Note: It will be created if it does not already exist!
    """
    # Check if the plugin.txt file (specifying required plugins) is specified
    PLUGIN_FILE = os.getenv('INVENTREE_PLUGIN_FILE')

    if not PLUGIN_FILE:
        # If not specified, look in the same directory as the configuration file
        config_dir = get_config_file().parent
        PLUGIN_FILE = config_dir.joinpath('plugins.txt')
    else:
        # Make sure we are using a modern Path object
        PLUGIN_FILE = Path(PLUGIN_FILE)

    if not PLUGIN_FILE.exists():
        logger.warning("Plugin configuration file does not exist")
        logger.info(f"Creating plugin file at '{PLUGIN_FILE}'")

        # If opening the file fails (no write permission, for example), then this will throw an error
        PLUGIN_FILE.write_text("# InvenTree Plugins (uses PIP framework to install)\n\n")

    return PLUGIN_FILE


def get_setting(environment_var, backup_val, default_value=None):
    """Helper function for retrieving a configuration setting value.

    - First preference is to look for the environment variable
    - Second preference is to look for the value of the settings file
    - Third preference is the default value
    """
    val = os.getenv(environment_var)

    if val is not None:
        return val

    if backup_val is not None:
        return backup_val

    return default_value
