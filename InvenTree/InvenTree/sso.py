"""Helper functions for Single Sign On functionality"""


import logging

from common.models import InvenTreeSetting
from InvenTree.helpers import str2bool

logger = logging.getLogger('inventree')


def get_provider_app(provider):
    """Return the SocialApp object for the given provider"""

    from allauth.socialaccount.models import SocialApp

    try:
        apps = SocialApp.objects.filter(provider__iexact=provider.id)
    except SocialApp.DoesNotExist:
        logger.warning("SSO SocialApp not found for provider '%s'", provider.id)
        return None

    if apps.count() > 1:
        logger.warning("Multiple SocialApps found for provider '%s'", provider.id)

    if apps.count() == 0:
        logger.warning("SSO SocialApp not found for provider '%s'", provider.id)

    return apps.first()


def check_provider(provider, raise_error=False):
    """Check if the given provider is correctly configured.

    To be correctly configured, the following must be true:

    - Provider must either have a registered SocialApp
    - Must have at least one site enabled
    """

    import allauth.app_settings

    # First, check that the provider is enabled
    app = get_provider_app(provider)

    if not app:
        return False

    if allauth.app_settings.SITES_ENABLED:
        # At least one matching site must be specified
        if not app.sites.exists():
            logger.error("SocialApp %s has no sites configured", app)
            return False

    # At this point, we assume that the provider is correctly configured
    return True


def provider_display_name(provider):
    """Return the 'display name' for the given provider"""

    if app := get_provider_app(provider):
        return app.name

    # Fallback value if app not found
    return provider.name


def login_enabled() -> bool:
    """Return True if SSO login is enabled"""
    return str2bool(InvenTreeSetting.get_setting('LOGIN_ENABLE_SSO'))


def registration_enabled() -> bool:
    """Return True if SSO registration is enabled"""
    return str2bool(InvenTreeSetting.get_setting('LOGIN_ENABLE_SSO_REG'))


def auto_registration_enabled() -> bool:
    """Return True if SSO auto-registration is enabled"""
    return str2bool(InvenTreeSetting.get_setting('LOGIN_SIGNUP_SSO_AUTO'))
