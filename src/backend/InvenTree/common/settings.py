"""User-configurable settings for the common app."""

from os import environ
from typing import Optional

from django.core.exceptions import AppRegistryNotReady

import InvenTree.ready


def global_setting_overrides() -> dict:
    """Return a dictionary of global settings overrides.

    These values are set via environment variables or configuration file.
    """
    from django.conf import settings

    if hasattr(settings, 'GLOBAL_SETTINGS_OVERRIDES'):
        return settings.GLOBAL_SETTINGS_OVERRIDES or {}

    return {}


def get_global_setting(key, backup_value=None, enviroment_key=None, **kwargs):
    """Return the value of a global setting using the provided key."""
    from common.models import InvenTreeSetting

    if enviroment_key:
        value = environ.get(enviroment_key)
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
    if not InvenTree.ready.canAppAccessDatabase():
        return False
    try:
        from common.models import InvenTreeSetting
        from common.setting.system import SystemSetId
    except AppRegistryNotReady:
        # App registry not ready, cannot set global warning
        return False

    # Get and write (if necessary) the current global settings warning
    global_dict = get_global_setting(SystemSetId.GLOBAL_WARNING, {}, create=False)
    if global_dict is None or not isinstance(global_dict, dict):
        global_dict = {}
    if key not in global_dict:
        global_dict[key] = options or True
        InvenTreeSetting.set_setting(
            SystemSetId.GLOBAL_WARNING, global_dict, change_user=None, create=True
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
