"""Helper functions for loading InvenTree configuration options."""

import datetime
import json
import logging
import os
import random
import shutil
import string
import sys
from pathlib import Path
from typing import Optional

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


def get_root_dir() -> Path:
    """Returns the InvenTree root directory."""
    return get_base_dir().parent.parent.parent


def inventreeInstaller() -> Optional[str]:
    """Returns the installer for the running codebase - if set or detectable."""
    load_version_file()

    # First look in the environment variables, e.g. if running in docker
    installer = os.environ.get('INVENTREE_PKG_INSTALLER', '')

    if installer:
        return str(installer)

    if is_true(os.environ.get('INVENTREE_DEVCONTAINER', 'False')):
        return 'DEV'

    if is_true(os.environ.get('INVENTREE_DOCKER', 'False')):
        return 'DOC'

    try:
        from django.conf import settings

        from InvenTree.version import main_commit

        if settings.DOCKER:
            return 'DOC'
        elif main_commit is not None:
            return 'GIT'
    except Exception:
        pass
    return None


def get_config_dir() -> Path:
    """Returns the InvenTree configuration directory depending on the install type."""
    if inst := inventreeInstaller():
        if inst == 'DOC':
            return Path('/home/inventree/data/').resolve()
        elif inst == 'DEV':
            return Path('/home/inventree/dev/').resolve()
        elif inst == 'PKG':
            return Path('/etc/inventree/').resolve()

    return get_root_dir().joinpath('config').resolve()


def get_testfolder_dir() -> Path:
    """Returns the InvenTree test folder directory."""
    return get_base_dir().joinpath('_testfolder').resolve()


def get_version_file() -> Path:
    """Returns the path of the InvenTree VERSION file. This does not ensure that the file exists."""
    return get_root_dir().joinpath('VERSION').resolve()


def ensure_dir(path: Path, storage=None) -> None:
    """Ensure that a directory exists.

    If it does not exist, create it.
    """
    from django.core.files.base import ContentFile
    from django.core.files.storage import Storage

    if storage and isinstance(storage, Storage):
        if not storage.exists(str(path)):
            storage.save(str(path / '.empty'), ContentFile(''))
        return

    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


def get_config_file(create=True) -> Path:
    """Returns the path of the InvenTree configuration file.

    Note: It will be created it if does not already exist!
    """
    conf_dir = get_config_dir()
    base_dir = get_base_dir()

    cfg_filename = os.getenv('INVENTREE_CONFIG_FILE')

    if cfg_filename:
        cfg_filename = Path(cfg_filename.strip()).resolve()
    elif get_base_dir().joinpath('config.yaml').exists():
        # If the config file is in the old directory, use that
        cfg_filename = base_dir.joinpath('config.yaml').resolve()
    else:
        # Config file is *not* specified - use the default
        cfg_filename = conf_dir.joinpath('config.yaml').resolve()

    if not cfg_filename.exists() and create:
        print(
            "InvenTree configuration file 'config.yaml' not found - creating default file"
        )
        ensure_dir(cfg_filename.parent)

        cfg_template = base_dir.joinpath('config_template.yaml')
        shutil.copyfile(cfg_template, cfg_filename)
        print(f'Created config file {cfg_filename}')

    check_config_dir('INVENTREE_CONFIG_FILE', cfg_filename, conf_dir)
    return cfg_filename


def load_config_data(set_cache: bool = False) -> map | None:
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

    with open(cfg_file, encoding='utf-8') as cfg:
        try:
            data = yaml.safe_load(cfg)
        except yaml.parser.ParserError as error:
            logger.error(
                "INVE-E13: Error reading InvenTree configuration file '%s': %s",
                cfg_file,
                error,
            )
            sys.exit(1)

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
        Typecast value or original value if typecasting failed.
    """
    # Force 'list' of strings
    if type is list:
        value = to_list(value)

    # Valid JSON string is required
    elif type is dict:
        value = to_dict(value)

    # Special handling for boolean typecasting
    elif type is bool:
        val = is_true(value)
        return val

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


def get_media_dir(create=True, error=True):
    """Return the absolute path for the 'media' directory (where uploaded files are stored)."""
    md = get_setting('INVENTREE_MEDIA_ROOT', 'media_root')

    if not md:
        if error:
            raise FileNotFoundError('INVENTREE_MEDIA_ROOT not specified')
        else:
            return None

    md = Path(md).resolve()

    if create:
        md.mkdir(parents=True, exist_ok=True)

    return md


def get_static_dir(create=True, error=True):
    """Return the absolute path for the 'static' directory (where static files are stored)."""
    sd = get_setting('INVENTREE_STATIC_ROOT', 'static_root')

    if not sd:
        if error:
            raise FileNotFoundError('INVENTREE_STATIC_ROOT not specified')
        else:
            return None

    sd = Path(sd).resolve()

    if create:
        sd.mkdir(parents=True, exist_ok=True)

    return sd


def get_backup_dir(create=True, error=True):
    """Return the absolute path for the backup directory."""
    bd = get_setting('INVENTREE_BACKUP_DIR', 'backup_dir')

    if not bd:
        if error:
            raise FileNotFoundError('INVENTREE_BACKUP_DIR not specified')
        else:
            return None

    bd = Path(bd).resolve()

    if create:
        bd.mkdir(parents=True, exist_ok=True)

    return bd


def get_plugin_file() -> Path:
    """Returns the path of the InvenTree plugins specification file.

    Note: It will be created if it does not already exist!
    """
    # Check if the plugin.txt file (specifying required plugins) is specified
    plugin_file = get_setting('INVENTREE_PLUGIN_FILE', 'plugin_file')

    if not plugin_file:
        # If not specified, look in the same directory as the configuration file
        config_dir = get_config_file().parent
        plugin_file = config_dir.joinpath('plugins.txt')
    else:
        # Make sure we are using a modern Path object
        plugin_file = Path(plugin_file)

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

    check_config_dir('INVENTREE_PLUGIN_FILE', plugin_file)
    return plugin_file


def get_plugin_dir():
    """Returns the path of the custom plugins directory."""
    return get_setting('INVENTREE_PLUGIN_DIR', 'plugin_dir')


def get_secret_key(return_path: bool = False) -> str | Path:
    """Return the secret key value which will be used by django.

    Following options are tested, in descending order of preference:

    A) Check for environment variable INVENTREE_SECRET_KEY => Use raw key data
    B) Check for environment variable INVENTREE_SECRET_KEY_FILE => Load key data from file
    C) Look for default key file "secret_key.txt"
    D) Create "secret_key.txt" if it does not exist

    Args:
        return_path (bool): If True, return the path to the secret key file instead of the key data.
    """
    # Look for environment variable
    if secret_key := get_setting('INVENTREE_SECRET_KEY', 'secret_key'):
        logger.info('SECRET_KEY loaded by INVENTREE_SECRET_KEY')  # pragma: no cover
        return str(secret_key)

    # Look for secret key file
    if secret_key_file := get_setting('INVENTREE_SECRET_KEY_FILE', 'secret_key_file'):
        secret_key_file = Path(secret_key_file).resolve()
    elif get_base_dir().joinpath('secret_key.txt').exists():
        secret_key_file = get_base_dir().joinpath('secret_key.txt')
    else:
        # Default location for secret key file
        secret_key_file = get_config_dir().joinpath('secret_key.txt').resolve()
    check_config_dir('INVENTREE_SECRET_KEY_FILE', secret_key_file)

    if not secret_key_file.exists():
        logger.info("Generating random key file at '%s'", secret_key_file)
        ensure_dir(secret_key_file.parent)

        # Create a random key file
        options = string.digits + string.ascii_letters + string.punctuation
        key = ''.join([random.choice(options) for _idx in range(100)])
        secret_key_file.write_text(key)

    if return_path:
        return secret_key_file

    logger.debug("Loading SECRET_KEY from '%s'", secret_key_file)
    return secret_key_file.read_text().strip()


def get_oidc_private_key(return_path: bool = False) -> str | Path:
    """Return the private key for OIDC authentication.

    Following options are tested, in descending order of preference:
    A) Check for environment variable INVENTREE_OIDC_PRIVATE_KEY or config yalue => Use raw key data
    B) Check for environment variable INVENTREE_OIDC_PRIVATE_KEY_FILE  or config value => Load key data from file
    C) Create "oidc.pem" if it does not exist
    """
    RSA_KEY = get_setting('INVENTREE_OIDC_PRIVATE_KEY', 'oidc_private_key')
    if RSA_KEY:
        logger.info('RSA_KEY loaded by INVENTREE_OIDC_PRIVATE_KEY')  # pragma: no cover
        return RSA_KEY

    # Look for private key file
    key_loc = Path(
        get_setting(
            'INVENTREE_OIDC_PRIVATE_KEY_FILE',
            'oidc_private_key_file',
            get_config_dir().joinpath('oidc.pem'),
        )
    )

    # Trying old default location
    if not key_loc.exists():
        old_def_path = get_base_dir().joinpath('oidc.pem')
        if old_def_path.exists():
            key_loc = old_def_path.resolve()

    check_config_dir('INVENTREE_OIDC_PRIVATE_KEY_FILE', key_loc)
    if key_loc.exists():
        return key_loc.read_text() if not return_path else key_loc
    else:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        # Default location for private key file
        logger.info("Generating oidc key file at '%s'", key_loc)
        ensure_dir(key_loc.parent)

        # Create a random key file
        new_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        # Write our key to disk for safe keeping
        with open(str(key_loc), 'wb') as f:
            f.write(
                new_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        return key_loc.read_text() if not return_path else key_loc


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
    """Return a dictionary of settings for the frontend interface."""
    # New settings
    frontend_settings = get_setting(
        'INVENTREE_FRONTEND_SETTINGS', 'frontend_settings', {}, typecast=dict
    )

    # Set the base URL for the user interface
    # This is the UI path e.g. '/web/'
    if 'base_url' not in frontend_settings:
        frontend_settings['base_url'] = (
            get_setting('INVENTREE_FRONTEND_URL_BASE', 'frontend_url_base', 'web')
            or 'web'
        )

    # If provided, specify the API host
    api_host = frontend_settings.get('api_host', None) or get_setting(
        'INVENTREE_FRONTEND_API_HOST', 'frontend_api_host', None
    )

    if api_host:
        frontend_settings['api_host'] = api_host

    # Set the server list
    frontend_settings['server_list'] = frontend_settings.get('server_list', [])

    # Set the debug flag
    frontend_settings['debug'] = debug

    if 'environment' not in frontend_settings:
        frontend_settings['environment'] = 'development' if debug else 'production'

    if (debug and 'show_server_selector' not in frontend_settings) or len(
        frontend_settings['server_list']
    ) == 0:
        # In debug mode, show server selector by default
        # If no servers are specified, show server selector
        frontend_settings['show_server_selector'] = True

    # Support compatibility with "legacy" URLs?
    try:
        frontend_settings['url_compatibility'] = bool(
            frontend_settings.get('url_compatibility', True)
        )
    except Exception:
        # If the value is not a boolean, set it to True
        frontend_settings['url_compatibility'] = True

    return frontend_settings


def check_config_dir(
    setting_name: str, current_path: Path, config_dir: Optional[Path] = None
) -> None:
    """Warn if the config directory is not used."""
    if not config_dir:
        config_dir = get_config_dir()

    if not current_path.is_relative_to(config_dir):
        logger.warning(
            "INVE-W10 - Config for '%s' not in recommended directory '%s'.",
            setting_name,
            config_dir,
        )

        try:
            from common.settings import GlobalWarningCode, set_global_warning

            set_global_warning(
                GlobalWarningCode.UNCOMMON_CONFIG, {'path': str(config_dir)}
            )
        except ModuleNotFoundError:  # pragma: no cover
            pass

    return


VERSION_LOADED = False
"""Flag to indicate if the VERSION file has been loaded in this process."""


def load_version_file():
    """Load the VERSION file if it exists and place the contents into the general execution environment.

    Returns:
        True if the VERSION file was loaded (now or previously), False otherwise.
    """
    global VERSION_LOADED
    if VERSION_LOADED:
        return True

    # Load the VERSION file if it exists
    from dotenv import load_dotenv

    version_file = get_version_file()
    if version_file.exists():
        load_dotenv(version_file)
        VERSION_LOADED = True
        return True
    return False
