"""Custom token authentication class for InvenTree API."""

import datetime

from django.utils.translation import gettext_lazy as _

from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication

from users.models import ApiToken


class ApiTokenAuthentication(TokenAuthentication):
    """Custom implementation of TokenAuthentication class, with custom features.

    Changes:
    - Tokens can be revoked
    - Tokens can expire
    """

    model = ApiToken

    def authenticate_credentials(self, key):
        """Adds additional checks to the default token authentication method."""
        # If this runs without error, then the token is valid (so far)
        (user, token) = super().authenticate_credentials(key)

        if token.revoked:
            raise exceptions.AuthenticationFailed(_('Token has been revoked'))

        if token.expired:
            raise exceptions.AuthenticationFailed(_('Token has expired'))

        if token.last_seen != datetime.date.today():
            # Update the last-seen date
            token.last_seen = datetime.date.today()
            token.save()

        return (user, token)
