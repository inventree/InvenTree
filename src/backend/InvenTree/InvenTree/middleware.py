"""Middleware for InvenTree."""

import sys
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth.middleware import PersistentRemoteUserMiddleware
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import resolve, reverse_lazy
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import is_same_domain

import structlog
from error_report.middleware import ExceptionProcessor

from common.settings import get_global_setting
from InvenTree.AllUserRequire2FAMiddleware import AllUserRequire2FAMiddleware
from InvenTree.cache import create_session_cache, delete_session_cache
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


# List of target URL endpoints where *do not* want to redirect to
urls = [
    reverse_lazy('account_login'),
    reverse_lazy('admin:login'),
    reverse_lazy('admin:logout'),
]

# Do not redirect requests to any of these paths
paths_ignore = ['/api/', '/auth/', settings.MEDIA_URL, settings.STATIC_URL]


class AuthRequiredMiddleware:
    """Check for user to be authenticated."""

    def __init__(self, get_response):
        """Save response object."""
        self.get_response = get_response

    def check_token(self, request) -> bool:
        """Check if the user is authenticated via token."""
        if token := get_token_from_request(request):
            # Does the provided token match a valid user?
            try:
                token = ApiToken.objects.get(key=token)

                if token.active and token.user:
                    # Provide the user information to the request
                    request.user = token.user
                    return True
            except ApiToken.DoesNotExist:
                logger.warning('Access denied for unknown token %s', token)

        return False

    def __call__(self, request):
        """Check if user needs to be authenticated and is.

        Redirects to login if not authenticated.
        """
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        assert hasattr(request, 'user')

        # API requests are handled by the DRF library
        if request.path_info.startswith('/api/'):
            return self.get_response(request)

        # oAuth2 requests are handled by the oAuth2 library
        if request.path_info.startswith('/o/'):
            return self.get_response(request)

        # anymail requests are handled by the anymail library
        if request.path_info.startswith('/anymail/'):
            return self.get_response(request)

        # Is the function exempt from auth requirements?
        path_func = resolve(request.path).func

        if getattr(path_func, 'auth_exempt', False) is True:
            return self.get_response(request)

        if not request.user.is_authenticated:
            """
            Normally, a web-based session would use csrftoken based authentication.

            However when running an external application (e.g. the InvenTree app or Python library),
            we must validate the user token manually.
            """

            authorized = False

            # Allow static files to be accessed without auth
            # Important for e.g. login page
            if (
                request.path_info.startswith('/static/')
                or request.path_info.startswith('/accounts/')
                or (
                    request.path_info.startswith(f'/{settings.FRONTEND_URL_BASE}/')
                    or request.path_info.startswith('/assets/')
                    or request.path_info == f'/{settings.FRONTEND_URL_BASE}'
                )
                or self.check_token(request)
            ):
                authorized = True

            # No authorization was found for the request
            if not authorized:
                path = request.path_info

                if path not in urls and not any(
                    path.startswith(p) for p in paths_ignore
                ):
                    # Save the 'next' parameter to pass through to the login view

                    return redirect(
                        f'{reverse_lazy("account_login")}?next={request.path}'
                    )
                # Return a 401 (Unauthorized) response code for this request
                return HttpResponse('Unauthorized', status=401)

        response = self.get_response(request)

        return response


class Check2FAMiddleware(AllUserRequire2FAMiddleware):
    """Ensure that mfa is enforced if set so."""

    def enforce_2fa(self, request):
        """Use setting to check if MFA should be enforced."""
        return get_global_setting('LOGIN_ENFORCE_MFA')


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
        if path in urls or any(path.startswith(p) for p in paths_ignore):
            return None

        # Ensure that the settings are set correctly with the current request
        accessed_scheme = request._current_scheme_host
        if accessed_scheme and not accessed_scheme.startswith(settings.SITE_URL):
            msg = f'INVE-E7: The used path `{accessed_scheme}` does not match the SITE_URL `{settings.SITE_URL}`'
            logger.error(msg)
            return render(
                request, 'config_error.html', {'error_message': msg}, status=500
            )

        # Check trusted origins
        referer = urlsplit(accessed_scheme)
        if not any(
            is_same_domain(referer.netloc, host)
            for host in [
                urlsplit(origin).netloc.lstrip('*')
                for origin in settings.CSRF_TRUSTED_ORIGINS
            ]
        ):
            msg = f'INVE-E7: The used path `{accessed_scheme}` is not in the TRUSTED_ORIGINS'
            logger.error(msg)
            return render(
                request, 'config_error.html', {'error_message': msg}, status=500
            )
        return None
