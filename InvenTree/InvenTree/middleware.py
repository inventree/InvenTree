from django.shortcuts import HttpResponseRedirect
from django.urls import reverse_lazy, Resolver404
from django.db import connection
from django.shortcuts import redirect
from django.conf.urls import include, url
import logging
import time
import operator

from rest_framework.authtoken.models import Token
from allauth_2fa.middleware import BaseRequire2FAMiddleware

from InvenTree.urls import frontendpatterns


logger = logging.getLogger("inventree")


class AuthRequiredMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
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
                        pass

            # No authorization was found for the request
            if not authorized:
                # A logout request will redirect the user to the login screen
                if request.path_info == reverse_lazy('account_logout'):
                    return HttpResponseRedirect(reverse_lazy('account_login'))

                path = request.path_info

                # List of URL endpoints we *do not* want to redirect to
                urls = [
                    reverse_lazy('account_login'),
                    reverse_lazy('account_logout'),
                    reverse_lazy('admin:login'),
                    reverse_lazy('admin:logout'),
                ]

                if path not in urls and not path.startswith('/api/'):
                    # Save the 'next' parameter to pass through to the login view

                    return redirect('%s?next=%s' % (reverse_lazy('account_login'), request.path))

        response = self.get_response(request)

        return response


class QueryCountMiddleware(object):
    """
    This middleware will log the number of queries run
    and the total time taken for each request (with a
    status code of 200). It does not currently support
    multi-db setups.

    To enable this middleware, set 'log_queries: True' in the local InvenTree config file.

    Reference: https://www.dabapps.com/blog/logging-sql-queries-django-13/

    Note: 2020-08-15 - This is no longer used, instead we now rely on the django-debug-toolbar addon
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        t_start = time.time()
        response = self.get_response(request)
        t_stop = time.time()

        if response.status_code == 200:
            total_time = 0

            if len(connection.queries) > 0:

                queries = {}

                for query in connection.queries:
                    query_time = query.get('time')

                    sql = query.get('sql').split('.')[0]

                    if sql in queries:
                        queries[sql] += 1
                    else:
                        queries[sql] = 1

                    if query_time is None:
                        # django-debug-toolbar monkeypatches the connection
                        # cursor wrapper and adds extra information in each
                        # item in connection.queries. The query time is stored
                        # under the key "duration" rather than "time" and is
                        # in milliseconds, not seconds.
                        query_time = float(query.get('duration', 0))

                    total_time += float(query_time)

                logger.debug('{n} queries run, {a:.3f}s / {b:.3f}s'.format(
                    n=len(connection.queries),
                    a=total_time,
                    b=(t_stop - t_start)))

                for x in sorted(queries.items(), key=operator.itemgetter(1), reverse=True):
                    print(x[0], ':', x[1])

        return response


url_matcher = url('', include(frontendpatterns))

class Check2FAMiddleware(BaseRequire2FAMiddleware):
    def require_2fa(self, request):
        # Superusers are require to have 2FA.
        try:
            if url_matcher.resolve(request.path[1:]):
                return True
        except Resolver404:
            pass
        return False
