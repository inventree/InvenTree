from django.shortcuts import HttpResponseRedirect
from django.urls import reverse_lazy
from django.db import connection
from django.shortcuts import redirect
import logging
import time
import operator

from rest_framework.authtoken.models import Token

logger = logging.getLogger("inventree")


class AuthRequiredMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        assert hasattr(request, 'user')

        response = self.get_response(request)

        if not request.user.is_authenticated:
            """
            Normally, a web-based session would use csrftoken based authentication.
            However when running an external application (e.g. the InvenTree app),
            we wish to use token-based auth to grab media files.

            So, we will allow token-based authentication but ONLY for the /media/ directory.

            What problem is this solving?
            - The InvenTree mobile app does not use csrf token auth
            - Token auth is used by the Django REST framework, but that is under the /api/ endpoint
            - Media files (e.g. Part images) are required to be served to the app
            - We do not want to make /media/ files accessible without login!

            There is PROBABLY a better way of going about this?
            a) Allow token-based authentication against a user?
            b) Serve /media/ files in a duplicate location e.g. /api/media/ ?
            c) Is there a "standard" way of solving this problem?

            My [google|stackoverflow]-fu has failed me. So this hack has been created.
            """

            authorized = False

            # Allow static files to be accessed without auth
            # Important for e.g. login page
            if request.path_info.startswith('/static/'):
                authorized = True

            # Unauthorized users can access the login page
            elif request.path_info.startswith('/accounts/'):
                authorized = True

            elif 'Authorization' in request.headers.keys():
                auth = request.headers['Authorization'].strip()

                if auth.startswith('Token') and len(auth.split()) == 2:
                    token = auth.split()[1]

                    # Does the provided token match a valid user?
                    if Token.objects.filter(key=token).exists():

                        allowed = ['/api/', '/media/']

                        # Only allow token-auth for /media/ or /static/ dirs!
                        if any([request.path_info.startswith(a) for a in allowed]):
                            authorized = True

            # No authorization was found for the request
            if not authorized:
                # A logout request will redirect the user to the login screen
                if request.path_info == reverse_lazy('logout'):
                    return HttpResponseRedirect(reverse_lazy('login'))

                login = reverse_lazy('login')

                if not request.path_info == login and not request.path_info.startswith('/api/'):
                    # Save the 'next' parameter to pass through to the login view

                    return redirect('%s?next=%s' % (login, request.path))

        # Code to be executed for each request/response after
        # the view is called.

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
