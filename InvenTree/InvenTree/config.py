"""Helper functions for loading InvenTree configuration options."""

import logging
import os
import shutil

logger = logging.getLogger('inventree')


def get_base_dir():
    """Returns the base (top-level) InvenTree directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_config_file():
    """Returns the path of the InvenTree configuration file.

    Note: It will be created it if does not already exist!
    """
    base_dir = get_base_dir()

    cfg_filename = os.getenv('INVENTREE_CONFIG_FILE')

    if cfg_filename:
        cfg_filename = cfg_filename.strip()
        cfg_filename = os.path.abspath(cfg_filename)
    else:
        # Config file is *not* specified - use the default
        cfg_filename = os.path.join(base_dir, 'config.yaml')

    if not os.path.exists(cfg_filename):
        print("InvenTree configuration file 'config.yaml' not found - creating default file")

        cfg_template = os.path.join(base_dir, "config_template.yaml")
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

        config_dir = os.path.dirname(get_config_file())

        PLUGIN_FILE = os.path.join(config_dir, 'plugins.txt')

    if not os.path.exists(PLUGIN_FILE):
        logger.warning("Plugin configuration file does not exist")
        logger.info(f"Creating plugin file at '{PLUGIN_FILE}'")

        # If opening the file fails (no write permission, for example), then this will throw an error
        with open(PLUGIN_FILE, 'w') as plugin_file:
            plugin_file.write("# InvenTree Plugins (uses PIP framework to install)\n\n")

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
