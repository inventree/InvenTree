"""Middleware for InvenTree."""

import sys
from typing import Optional
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth.middleware import PersistentRemoteUserMiddleware
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import resolve, reverse, reverse_lazy
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import is_same_domain
from django.utils.translation import gettext_lazy as _

import structlog
from error_report.middleware import ExceptionProcessor

from common.settings import get_global_setting
from InvenTree.cache import create_session_cache, delete_session_cache
from InvenTree.config import CONFIG_LOOKUPS, inventreeInstaller
from users.models import ApiToken

logger = structlog.get_logger('inventree')


def get_token_from_request(request):
    """Extract token information from a request object."""
    auth_keys = ['Authorization', 'authorization']
    token_keys = ['token', 'bearer']

    for k in auth_keys:
        if auth_header := request.headers.get(k, None):
            auth_header = auth_header.strip().lower().split()

            if len(auth_header) > 1:
                if auth_header[0].strip().lower().replace(':', '') in token_keys:
                    token = auth_header[1]
                    return token

    return None


def ensure_slashes(path: str):
    """Ensure that slashes are suroudning the passed path."""
    if not path.startswith('/'):
        path = f'/{path}'
    if not path.endswith('/'):
        path = f'{path}/'
    return path


# List of target URL endpoints where *do not* want to redirect to
urls = [
    reverse_lazy('account_login'),
    reverse_lazy('admin:login'),
    reverse_lazy('admin:logout'),
]

paths_ignore_handling = [
    '/api/',
    reverse('auth-check'),
    settings.MEDIA_URL,
    settings.STATIC_URL,
]
"""Paths that should not use InvenTrees own auth rejection behaviour, no host checking or redirecting. Security
 are still enforced."""
paths_own_security = [
    '/api/',  # DRF handles API
    '/o/',  # oAuth2 library - has its own auth model
    '/anymail/',  # Mails - wehbhooks etc
    '/accounts/',  # allauth account management - has its own auth model
    '/assets/',  # Web assets - only used for testing, no security model needed
    ensure_slashes(
        settings.STATIC_URL
    ),  # Static files  - static files are considered safe to serve
    ensure_slashes(
        settings.FRONTEND_URL_BASE
    ),  # Frontend files - frontend paths have their own security model
]
"""Paths that handle their own security model."""
pages_mfa_bypass = [
    'api-user-meta',
    'api-user-me',
    'api-user-roles',
    'api-inventree-info',
    'api-token',
    # web platform urls
    'password_reset_confirm',
    'index',
    'web',
    'web-wildcard',
    'web-assets',
]
"""Exact page names that bypass MFA enforcement - normal security model is still enforced."""
apps_mfa_bypass = [
    'headless'  # Headless allauth app - has its own security model
]
"""App namespaces that bypass MFA enforcement - normal security model is still enforced."""


class AuthRequiredMiddleware:
    """Check for user to be authenticated."""

    def __init__(self, get_response):
        """Save response object."""
        self.get_response = get_response

    def check_token(self, request) -> bool:
        """Check if the user is authenticated via token."""
        if token := get_token_from_request(request):
            request.token = token
            # Does the provided token match a valid user?
            try:
                token = ApiToken.objects.get(key=token)

                if token.active and token.user:
                    # Provide the user information to the request
                    request.user = token.user
                    return True
            except ApiToken.DoesNotExist:  # pragma: no cover
                logger.warning(
                    'Access denied for unknown token %s', token
                )  # pragma: no cover

        return False

    def __call__(self, request):
        """Check if user needs to be authenticated and is.

        Redirects to login if not authenticated.
        """
        path: str = request.path_info
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        assert hasattr(request, 'user')

        # API requests that are handled elsewhere
        if any(path.startswith(a) for a in paths_own_security):
            return self.get_response(request)

        # Is the function exempt from auth requirements?
        path_func = resolve(request.path).func
        if getattr(path_func, 'auth_exempt', False) is True:
            return self.get_response(request)

        if not request.user.is_authenticated and not (
            path == f'/{settings.FRONTEND_URL_BASE}' or self.check_token(request)
        ):
            """
            Normally, a web-based session would use csrftoken based authentication.

            However when running an external application (e.g. the InvenTree app or Python library),
            we must validate the user token manually.
            """
            if path not in urls and not any(
                path.startswith(p) for p in paths_ignore_handling
            ):
                # Save the 'next' parameter to pass through to the login view

                return redirect(f'{reverse_lazy("account_login")}?next={request.path}')
            # Return a 401 (Unauthorized) response code for this request
            return HttpResponse('Unauthorized', status=401)

        response = self.get_response(request)
        return response


class Check2FAMiddleware(MiddlewareMixin):
    """Ensure that users have two-factor authentication enabled before they have access restricted endpoints.

    Adapted from https://github.com/pennersr/django-allauth/issues/3649
    """

    require_2fa_message = _(
        'You must enable two-factor authentication before doing anything else.'
    )

    def on_require_2fa(self, request: HttpRequest) -> HttpResponse:
        """Force user to mfa activation."""
        return JsonResponse(
            {'id': 'mfa_register', 'error': self.require_2fa_message}, status=401
        )

    def is_allowed_page(self, request: HttpRequest) -> bool:
        """Check if the current page can be accessed without mfa."""
        match = request.resolver_match
        return (
            False
            if match is None
            else any(ref in apps_mfa_bypass for ref in match.app_names)
            or match.url_name in pages_mfa_bypass
            or match.route == 'favicon.ico'
        )

    def is_multifactor_logged_in(self, request: HttpRequest) -> bool:
        """Check if the user is logged in with multifactor authentication."""
        from allauth.account.authentication import get_authentication_records
        from allauth.mfa.utils import is_mfa_enabled
        from allauth.mfa.webauthn.internal.flows import did_use_passwordless_login

        authns = get_authentication_records(request)

        return is_mfa_enabled(request.user) and (
            did_use_passwordless_login(request)
            or any(record.get('method') == 'mfa' for record in authns)
        )

    def process_view(
        self, request: HttpRequest, view_func, view_args, view_kwargs
    ) -> Optional[HttpResponse]:
        """Determine if the server is set up enforce 2fa registration."""
        from django.conf import settings

        # Exit early if MFA is not enabled
        if not settings.MFA_ENABLED:
            return None

        if request.user.is_anonymous:
            return None
        if self.is_allowed_page(request):
            return None
        if self.is_multifactor_logged_in(request):
            return None
        if getattr(
            request, 'token', get_token_from_request(request)
        ):  # Token based login can not do MFA
            return None

        if self.enforce_2fa(request):
            return self.on_require_2fa(request)
        return None

    def enforce_2fa(self, request):
        """Use setting to check if MFA should be enforced."""
        return get_global_setting(
            'LOGIN_ENFORCE_MFA', None, 'INVENTREE_LOGIN_ENFORCE_MFA'
        )


class InvenTreeRemoteUserMiddleware(PersistentRemoteUserMiddleware):
    """Middleware to check if HTTP-header based auth is enabled and to set it up."""

    header = settings.REMOTE_LOGIN_HEADER

    def process_request(self, request):
        """Check if proxy login is enabled."""
        if not settings.REMOTE_LOGIN:
            return

        return super().process_request(request)


class InvenTreeExceptionProcessor(ExceptionProcessor):
    """Custom exception processor that respects blocked errors."""

    def process_exception(self, request, exception):
        """Check if kind is ignored before processing."""
        kind, _info, _data = sys.exc_info()

        # Check if the error is on the ignore list
        if kind in settings.IGNORED_ERRORS:
            return

        from error_report.settings import ERROR_DETAIL_SETTINGS

        # Error reporting is disabled
        if not ERROR_DETAIL_SETTINGS.get('ERROR_DETAIL_ENABLE', True):
            return

        path = request.build_absolute_uri()

        # Truncate the path to a reasonable length
        # Otherwise we get a database error,
        # because the path field is limited to 200 characters
        if len(path) > 200:
            path = path[:195] + '...'

        # Pass off to the exception reporter
        from InvenTree.exceptions import log_error

        log_error(path)


class InvenTreeRequestCacheMiddleware(MiddlewareMixin):
    """Middleware to perform caching against the request object.

    This middleware is used to cache data against the request object,
    which can be used to store data for the duration of the request.

    In this fashion, we can avoid hitting the external cache multiple times,
    much less the database!
    """

    def process_request(self, request):
        """Create a request-specific cache object."""
        create_session_cache(request)

    def process_response(self, request, response):
        """Clear the cache object."""
        delete_session_cache()
        return response


class InvenTreeHostSettingsMiddleware(MiddlewareMixin):
    """Middleware to check the host settings.

    Especially SITE_URL, trusted_origins.
    """

    def process_request(self, request):
        """Check the host settings."""
        # Debug setups do not enforce these checks so we ignore that case
        if settings.DEBUG:
            return None

        # Handle commonly ignored paths that might also work without a correct setup (api, auth)
        path = request.path_info
        if path in urls or any(path.startswith(p) for p in paths_ignore_handling):
            return None

        # treat the accessed scheme and host
        accessed_scheme = request._current_scheme_host
        referer = urlsplit(accessed_scheme)

        site_url = urlsplit(settings.SITE_URL)

        # Check if the accessed URL matches the SITE_URL setting
        site_url_match = (
            (
                # Exact match on domain
                is_same_domain(referer.netloc, site_url.netloc)
                and referer.scheme == site_url.scheme
            )
            or (
                # Lax protocol match, accessed URL starts with SITE_URL
                settings.SITE_LAX_PROTOCOL_CHECK
                and accessed_scheme.startswith(settings.SITE_URL)
            )
            or (
                # Lax protocol match, same domain
                settings.SITE_LAX_PROTOCOL_CHECK
                and referer.hostname == site_url.hostname
            )
        )

        if not site_url_match:
            # The accessed URL does not match the SITE_URL setting
            if (
                isinstance(settings.CSRF_TRUSTED_ORIGINS, list)
                and len(settings.CSRF_TRUSTED_ORIGINS) > 1
            ):
                # The used url might not be the primary url - next check determines if in a trusted origins
                pass
            else:
                source = CONFIG_LOOKUPS.get('INVENTREE_SITE_URL', {}).get(
                    'source', 'unknown'
                )
                dpl_method = inventreeInstaller()
                msg = f'INVE-E7: The visited path `{accessed_scheme}` does not match the SITE_URL `{settings.SITE_URL}`. The INVENTREE_SITE_URL is set via `{source}` config method - deployment method `{dpl_method}`'
                logger.error(msg)
                return render(
                    request, 'config_error.html', {'error_message': msg}, status=500
                )

        trusted_origins_match = (
            # Matching domain found in allowed origins
            any(
                is_same_domain(referer.netloc, host)
                for host in [
                    urlsplit(origin).netloc.lstrip('*')
                    for origin in settings.CSRF_TRUSTED_ORIGINS
                ]
            )
        ) or (
            # Lax protocol match allowed
            settings.SITE_LAX_PROTOCOL_CHECK
            and any(
                referer.hostname == urlsplit(origin).hostname
                for origin in settings.CSRF_TRUSTED_ORIGINS
            )
        )

        # Check trusted origins
        if not trusted_origins_match:
            msg = f'INVE-E7: The used path `{accessed_scheme}` is not in the TRUSTED_ORIGINS'
            logger.error(msg)
            return render(
                request, 'config_error.html', {'error_message': msg}, status=500
            )

        # All checks passed
        return None
