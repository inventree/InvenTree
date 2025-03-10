"""Middleware to require 2FA for users."""

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext_lazy as _

from allauth.account.authentication import get_authentication_records
from allauth.mfa.utils import is_mfa_enabled
from allauth.mfa.webauthn.internal.flows import did_use_passwordless_login


def is_multifactor_logged_in(request: HttpRequest) -> bool:
    """Check if the user is logged in with multifactor authentication."""
    authns = get_authentication_records(request)

    return is_mfa_enabled(request.user) and (
        did_use_passwordless_login(request)
        or any(record.get('method') == 'mfa' for record in authns)
    )


class AllUserRequire2FAMiddleware(MiddlewareMixin):
    """Ensure that users have two-factor authentication enabled before they have access restricted endpoints.

    Adapted from https://github.com/pennersr/django-allauth/issues/3649
    """

    allowed_pages = [
        'api-user-meta',
        'api-user-me',
        'api-user-roles',
        'api-inventree-info',
        'api-token',
        # web platform urls
        'password_reset_confirm',
        'platform',
        'platform-wildcard',
        'web-assets',
    ]
    app_names = ['headless']
    require_2fa_message = _(
        'You must enable two-factor authentication before doing anything else.'
    )

    def on_require_2fa(self, request: HttpRequest) -> HttpResponse:
        """Force user to mfa activation."""
        return JsonResponse({'id': 'mfa_register'}, status=401)

    def is_allowed_page(self, request: HttpRequest) -> bool:
        """Check if the current page can be accessed without mfa."""
        return (
            any(ref in self.app_names for ref in request.resolver_match.app_names)
            or request.resolver_match.url_name in self.allowed_pages
            or request.resolver_match.route == 'favicon.ico'
        )

    def enforce_2fa(self, request):
        """Check if 2fa should be enforced for this request."""
        return True

    def process_view(
        self, request: HttpRequest, view_func, view_args, view_kwargs
    ) -> HttpResponse:
        """If set up enforce 2fa registration."""
        if request.user.is_anonymous:
            return None
        if self.is_allowed_page(request):
            return None
        if is_multifactor_logged_in(request):
            return None

        if self.enforce_2fa(request):
            return self.on_require_2fa(request)
        return None
