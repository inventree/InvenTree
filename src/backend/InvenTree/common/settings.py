"""User-configurable settings for the common app."""

import json
from os import environ
from typing import Optional

from django.core.exceptions import AppRegistryNotReady

import structlog

import InvenTree.ready

logger = structlog.get_logger('inventree')


def global_setting_overrides() -> dict:
    """Return a dictionary of global settings overrides.

    These values are set via environment variables or configuration file.
    """
    from django.conf import settings

    if hasattr(settings, 'GLOBAL_SETTINGS_OVERRIDES'):
        return settings.GLOBAL_SETTINGS_OVERRIDES or {}

    return {}


def get_global_setting(key, backup_value=None, environment_key=None, **kwargs):
    """Return the value of a global setting using the provided key."""
    from common.models import InvenTreeSetting

    if environment_key:
        value = environ.get(environment_key)
        if value:
            return value

    if backup_value is not None:
        kwargs['backup_value'] = backup_value

    return InvenTreeSetting.get_setting(key, **kwargs)


def set_global_setting(key, value, change_user=None, create=True, **kwargs):
    """Set the value of a global setting using the provided key."""
    from common.models import InvenTreeSetting

    kwargs['change_user'] = change_user
    kwargs['create'] = create

    return InvenTreeSetting.set_setting(key, value, **kwargs)


class GlobalWarningCode:
    """Warning codes that reflect to the status of the instance."""

    UNCOMMON_CONFIG = 'INVE-W10'
    TEST_KEY = '_TEST'


def set_global_warning(key: str, options: Optional[dict] = None) -> bool:
    """Set a global warning for a code.

    Args:
        key (str): The key for the warning.
        options (dict or bool): Options for the warning, or True to set a default warning.

    Raises:
        ValueError: If the key is not provided.

    Returns:
        bool: True if the warning was checked / set successfully, False if no check was performed.
    """
    if not key:
        raise ValueError('Key must be provided for global warning setting.')

    # Ensure DB is ready
    if not InvenTree.ready.canAppAccessDatabase(allow_test=True):
        return False
    try:
        from common.models import InvenTreeSetting
        from common.setting.system import SystemSetId
    except AppRegistryNotReady:
        # App registry not ready, cannot set global warning
        return False

    # Get and write (if necessary) the current global settings warning
    global_dict = get_global_setting(SystemSetId.GLOBAL_WARNING, '{}', create=False)
    try:
        global_dict = json.loads(global_dict)
    except json.JSONDecodeError:
        global_dict = {}
    if global_dict is None or not isinstance(global_dict, dict):
        global_dict = {}
    if key not in global_dict or global_dict[key] != options:
        global_dict[key] = options if options is not None else True
        try:
            global_dict_val = json.dumps(global_dict)
        except TypeError:
            # If the options cannot be serialized, we will set an empty the warning
            global_dict_val = 'true'
            logger.warning(
                f'Failed to serialize global warning options for key "{key}". Setting to True.'
            )
        InvenTreeSetting.set_setting(
            SystemSetId.GLOBAL_WARNING, global_dict_val, change_user=None, create=True
        )
    return True


def stock_expiry_enabled():
    """Returns True if the stock expiry feature is enabled."""
    from common.models import InvenTreeSetting

    return InvenTreeSetting.get_setting('STOCK_ENABLE_EXPIRY', False, create=False)


def prevent_build_output_complete_on_incompleted_tests():
    """Returns True if the completion of the build outputs is disabled until the required tests are passed."""
    from common.models import InvenTreeSetting

    return InvenTreeSetting.get_setting(
        'PREVENT_BUILD_COMPLETION_HAVING_INCOMPLETED_TESTS', False, create=False
    )
