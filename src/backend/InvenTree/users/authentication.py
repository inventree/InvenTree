"""Custom token authentication class for InvenTree API."""

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from allauth.mfa.utils import is_mfa_enabled
from oauth2_provider.contrib.rest_framework import OAuth2ProtectedResourceAuthentication
from rest_framework import exceptions
from rest_framework.authentication import BasicAuthentication, TokenAuthentication

import InvenTree.helpers
import users.models
from common.settings import get_global_setting


def mfa_enforced() -> bool:
    """Check if MFA is enforced globally for all users."""
    return bool(
        settings.MFA_ENABLED
        and get_global_setting('LOGIN_ENFORCE_MFA', None, 'INVENTREE_LOGIN_ENFORCE_MFA')
    )


def password_auth_allowed(user) -> bool:
    """Check if a password alone is allowed to authenticate the user."""
    if is_mfa_enabled(user):
        return False
    return not mfa_enforced()


class InvenTreeBasicAuthentication(BasicAuthentication):
    """Custom basic auth class.

    Checks:
    - If MFA is required and disallows basic auth
    - Only works if BASIC_AUTH_ENABLED is True
    """

    def authenticate(self, request):
        """Only attempt basic authentication if it is enabled."""
        if not settings.BASIC_AUTH_ENABLED:
            return None
        return super().authenticate(request)

    def authenticate_header(self, request):
        """Only advertise basic authentication if it is enabled."""
        if not settings.BASIC_AUTH_ENABLED:
            return ''
        return super().authenticate_header(request)

    def authenticate_credentials(self, userid, password, request=None):
        """Also check if MFA is required for the user."""
        user, auth = super().authenticate_credentials(userid, password, request)

        if not password_auth_allowed(user):
            raise exceptions.AuthenticationFailed(
                _('INVE-W20: Password authentication not allowed due to MFA')
            )

        return (user, auth)


def validate_api_token(raw_token: str) -> users.models.ApiToken:
    """Look up and fully validate a raw API token value.

    This is the single source of truth for API token validation,
    used by both the DRF authentication class and the middleware stack.

    Raises:
        AuthenticationFailed: If the token is unknown, revoked, expired, belongs to an inactive user,
            or belongs to a user without MFA while MFA is enforced
    """
    token = users.models.ApiToken.get_from_string(raw_token) if raw_token else None

    if token is None or token.user is None:
        raise exceptions.AuthenticationFailed(_('Invalid token.'))

    if not token.user.is_active:
        raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))

    if token.revoked:
        raise exceptions.AuthenticationFailed(_('Token has been revoked'))

    if token.expired:
        raise exceptions.AuthenticationFailed(_('Token has expired'))

    # Tokens issued before MFA was enforced must not outlive the enforcement
    if mfa_enforced() and not is_mfa_enabled(token.user):
        raise exceptions.AuthenticationFailed(
            _('Multi-factor authentication must be enabled for this account')
        )

    today = InvenTree.helpers.current_date()

    if token.last_seen != today:
        # Update the last-seen date
        # Note: Use update_fields to avoid clobbering concurrent changes to
        # other fields on this token (e.g. a concurrent revocation)
        token.last_seen = today
        token.save(update_fields=['last_seen'])

    return token


class ApiTokenAuthentication(TokenAuthentication):
    """Custom implementation of TokenAuthentication class, with custom features.

    Changes:
    - Tokens can be revoked
    - Tokens can expire
    """

    model = users.models.ApiToken

    def authenticate_credentials(self, key):
        """Adds additional checks to the default token authentication method."""
        token = validate_api_token(key)
        return (token.user, token)


class ExtendedOAuth2Authentication(OAuth2ProtectedResourceAuthentication):
    """Custom implementation of OAuth2Authentication class to support custom scope rendering."""

    def authenticate(self, request):
        """Authenticate the request, if the requested view enforces OAuth2 token scopes."""
        result = super().authenticate(request)

        if result is not None and not self.view_enforces_scopes(request):
            raise exceptions.PermissionDenied(
                _('OAuth2 tokens are not accepted for this endpoint')
            )

        return result

    def view_enforces_scopes(self, request) -> bool:
        """Check if any permission class of the requested view enforces OAuth2 token scopes."""
        from InvenTree.permissions import OASTokenMixin

        view = (getattr(request, 'parser_context', None) or {}).get('view')

        return view is not None and any(
            isinstance(permission, OASTokenMixin)
            for permission in view.get_permissions()
        )
