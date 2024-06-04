"""User-configurable settings for the common app."""


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
