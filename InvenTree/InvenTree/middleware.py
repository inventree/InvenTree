from django.shortcuts import HttpResponseRedirect
from django.urls import reverse_lazy


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