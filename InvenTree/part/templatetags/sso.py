"""This module provides template tags pertaining to SSO functionality"""


from django import template

from common.models import InvenTreeSetting
from InvenTree.helpers import str2bool

register = template.Library()


@register.simple_tag()
def sso_login_enabled():
    """Return True if single-sign-on is enabled"""

    val = InvenTreeSetting.get_setting('LOGIN_ENABLE_SSO')

    print("SSO Enabled:", val)

    return str2bool(InvenTreeSetting.get_setting('LOGIN_ENABLE_SSO'))


@register.simple_tag()
def sso_reg_enabled():
    """Return True if single-sign-on is enabled for self-registration"""
    return str2bool(InvenTreeSetting.get_setting('LOGIN_ENABLE_SSO_REG'))


@register.simple_tag()
def sso_auto_enabled():
    """Return True if single-sign-on is enabled for auto-registration"""
    return str2bool(InvenTreeSetting.get_setting('LOGIN_SIGNUP_SSO_AUTO'))


@register.simple_tag()
def sso_check_provider(provider):
    """Return True if the given provider is correctly configured"""

    from allauth.socialaccount.models import SocialApp

    # First, check that the provider is enabled
    if not SocialApp.objects.filter(provider__iexact=provider.name).exists():
        return False

    # Next, check that the provider is correctly configured

    # At this point, we assume that the provider is correctly configured
    return True
