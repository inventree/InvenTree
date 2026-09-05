"""Authentication for the SCIM provisioning endpoint.

The SCIM endpoint is *not* authenticated against InvenTree user accounts.
Instead, a single bearer secret is generated on-demand from the Admin Center
(see `scim.api`) and is used by the external Identity Provider to
authenticate every SCIM request. Only an HMAC digest of that secret is ever
stored - see `scim.models.ScimConfiguration`.
"""

from django.utils.translation import gettext_lazy as _

from rest_framework import authentication, exceptions

from scim.models import ScimConfiguration


class ScimServiceUser:
    """Lightweight stand-in for a Django user, representing the SCIM integration itself.

    The SCIM protocol is authenticated via a shared bearer secret rather than
    as any particular InvenTree user account, so a full User instance would be
    misleading here. This object satisfies the minimal interface that DRF and
    InvenTree's request handling expect from `request.user`.
    """

    is_authenticated = True
    is_anonymous = False
    is_active = True
    is_staff = False
    is_superuser = False
    pk = None
    id = None
    username = 'scim-provisioning'

    def __str__(self):
        """String representation of the SCIM service user."""
        return self.username  # pragma: no cover


class ScimBearerAuthentication(authentication.BaseAuthentication):
    """DRF authentication class which validates the SCIM bearer secret.

    Expects an `Authorization: Bearer <secret>` header. The provided secret is
    hashed (HMAC-SHA256, seeded with the Django `SECRET_KEY`) and compared
    against the stored digest using a constant-time comparison.
    """

    www_authenticate_realm = 'scim'

    def authenticate(self, request):
        """Validate the bearer token against the configured SCIM secret."""
        header = authentication.get_authorization_header(request).split()

        if not header or header[0].lower() != b'bearer':
            return None

        if len(header) != 2:
            raise exceptions.AuthenticationFailed(
                _('Invalid SCIM authorization header')
            )

        secret = header[1].decode('utf-8')
        config = ScimConfiguration.load()

        if not config.verify_secret(secret):
            raise exceptions.AuthenticationFailed(_('Invalid SCIM bearer token'))

        config.mark_used()

        return (ScimServiceUser(), None)
