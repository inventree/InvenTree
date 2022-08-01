"""Middleware for InvenTree."""

import logging
import sys

from django.conf import settings
from django.contrib.auth.middleware import PersistentRemoteUserMiddleware
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import Resolver404, include, re_path, reverse_lazy

from allauth_2fa.middleware import (AllauthTwoFactorMiddleware,
                                    BaseRequire2FAMiddleware)
from error_report.middleware import ExceptionProcessor
from rest_framework.authtoken.models import Token

from common.models import InvenTreeSetting
from InvenTree.urls import frontendpatterns

logger = logging.getLogger("inventree")


class AuthRequiredMiddleware(object):
    """Check for user to be authenticated."""

    def __init__(self, get_response):
        """Save response object."""
        self.get_response = get_response

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

        if not request.user.is_authenticated:
            """
            Normally, a web-based session would use csrftoken based authentication.

            However when running an external application (e.g. the InvenTree app or Python library),
            we must validate the user token manually.
            """

            authorized = False

            # Allow static files to be accessed without auth
            # Important for e.g. login page
            if request.path_info.startswith('/static/'):
                authorized = True

            # Unauthorized users can access the login page
            elif request.path_info.startswith('/accounts/'):
                authorized = True

            elif 'Authorization' in request.headers.keys() or 'authorization' in request.headers.keys():
                auth = request.headers.get('Authorization', request.headers.get('authorization')).strip()

                if auth.lower().startswith('token') and len(auth.split()) == 2:
                    token_key = auth.split()[1]

                    # Does the provided token match a valid user?
                    try:
                        token = Token.objects.get(key=token_key)

                        # Provide the user information to the request
                        request.user = token.user
                        authorized = True

                    except Token.DoesNotExist:
                        logger.warning(f"Access denied for unknown token {token_key}")

            # No authorization was found for the request
            if not authorized:
                path = request.path_info

                # List of URL endpoints we *do not* want to redirect to
                urls = [
                    reverse_lazy('account_login'),
                    reverse_lazy('account_logout'),
                    reverse_lazy('admin:login'),
                    reverse_lazy('admin:logout'),
                ]

                # Do not redirect requests to any of these paths
                paths_ignore = [
                    '/api/',
                    '/js/',
                    '/media/',
                    '/static/',
                ]

                if path not in urls and not any([path.startswith(p) for p in paths_ignore]):
                    # Save the 'next' parameter to pass through to the login view

                    return redirect(f'{reverse_lazy("account_login")}?next={request.path}')

                else:
                    # Return a 401 (Unauthorized) response code for this request
                    return HttpResponse('Unauthorized', status=401)

        response = self.get_response(request)

        return response


url_matcher = re_path('', include(frontendpatterns))


class Check2FAMiddleware(BaseRequire2FAMiddleware):
    """Check if user is required to have MFA enabled."""
    def require_2fa(self, request):
        """Use setting to check if MFA should be enforced for frontend page."""
        try:
            if url_matcher.resolve(request.path[1:]):
                return InvenTreeSetting.get_setting('LOGIN_ENFORCE_MFA')
        except Resolver404:
            pass
        return False


class CustomAllauthTwoFactorMiddleware(AllauthTwoFactorMiddleware):
    """This function ensures only frontend code triggers the MFA auth cycle."""
    def process_request(self, request):
        """Check if requested url is forntend and enforce MFA check."""
        try:
            if not url_matcher.resolve(request.path[1:]):
                super().process_request(request)
        except Resolver404:
            pass


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
        """Check if kind is ignored before procesing."""
        kind, info, data = sys.exc_info()

        # Check if the eror is on the ignore list
        if kind in settings.IGNORED_ERRORS:
            return

        return super().process_exception(request, exception)
