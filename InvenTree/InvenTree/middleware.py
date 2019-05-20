from django.shortcuts import HttpResponseRedirect
from django.urls import reverse_lazy
from django.db import connection
import logging
import time

logger = logging.getLogger(__name__)


class AuthRequiredMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        assert hasattr(request, 'user')

        response = self.get_response(request)

        if not request.user.is_authenticated:
            print(request.path_info)

            if not request.path_info == reverse_lazy('login'):
                return HttpResponseRedirect(reverse_lazy('login'))

        # Code to be executed for each request/response after
        # the view is called.

        return response


class QueryCountMiddleware(object):
    """
    This middleware will log the number of queries run
    and the total time taken for each request (with a
    status code of 200). It does not currently support
    multi-db setups.

    Reference: https://www.dabapps.com/blog/logging-sql-queries-django-13/
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

                for query in connection.queries:
                    query_time = query.get('time')

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
                    
        return response
