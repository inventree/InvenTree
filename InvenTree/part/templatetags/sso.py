"""This module provides template tags pertaining to SSO functionality"""

from django import template

import InvenTree.sso

register = template.Library()


@register.simple_tag()
def sso_login_enabled():
    """Return True if single-sign-on is enabled"""
    return InvenTree.sso.login_enabled()


@register.simple_tag()
def sso_reg_enabled():
    """Return True if single-sign-on is enabled for self-registration"""
    return InvenTree.sso.registration_enabled()


@register.simple_tag()
def sso_auto_enabled():
    """Return True if single-sign-on is enabled for auto-registration"""
    return InvenTree.sso.auto_registration_enabled()


@register.simple_tag()
def sso_check_provider(provider):
    """Return True if the given provider is correctly configured"""

    return InvenTree.sso.check_provider(provider)
