"""Overrides for registration view."""

from django.utils.translation import gettext_lazy as _

from allauth.account import app_settings as allauth_account_settings
from dj_rest_auth.app_settings import api_settings
from dj_rest_auth.registration.views import RegisterView


class CustomRegisterView(RegisterView):
    """Registers a new user.

    Accepts the following POST parameters: username, email, password1, password2.
    """

    # Fixes https://github.com/inventree/InvenTree/issues/8707
    # This contains code from dj-rest-auth 7.0 - therefore the version was pinned
    def get_response_data(self, user):
        """Override to fix check for auth_model."""
        if (
            allauth_account_settings.EMAIL_VERIFICATION
            == allauth_account_settings.EmailVerificationMethod.MANDATORY
        ):
            return {'detail': _('Verification e-mail sent.')}

        if api_settings.USE_JWT:
            data = {
                'user': user,
                'access': self.access_token,
                'refresh': self.refresh_token,
            }
            return api_settings.JWT_SERIALIZER(
                data, context=self.get_serializer_context()
            ).data
        elif self.token_model:
            # Only change in this block is below
            return api_settings.TOKEN_SERIALIZER(
                user.api_tokens.last(), context=self.get_serializer_context()
            ).data
        return None
