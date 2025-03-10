"""User-configurable settings for the common app."""

from os import environ


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
