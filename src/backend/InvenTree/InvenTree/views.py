"""Various Views which provide extra functionality over base Django Views.

In particular these views provide base functionality for rendering Django forms
as JSON objects and passing them to modal forms (using jQuery / bootstrap).
"""

from urllib.parse import quote

from django.conf import settings
from django.http import HttpResponse
from django.views.generic import RedirectView

from InvenTree.helpers import pui_url


class AccountLoginRedirectView(RedirectView):
    """Redirect ``/accounts/login/`` into the SPA, keeping the ``next`` target.

    The target is recovered by LoggedIn.tsx after login; only relative
    in-app paths are forwarded, to prevent open redirects.
    """

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """Return the URL to redirect to."""
        next_url = self.request.GET.get('next', '')

        if next_url.startswith('/') and not next_url.startswith('//'):
            parts = next_url.strip('/').split('/')
            if len(parts) == 2 and parts[0] == 'build' and parts[1].isdigit():
                next_url = f'/manufacturing/build-order/{parts[1]}/'
            return f'{pui_url("logged-in/")}?next={quote(next_url, safe="")}'

        return f'/{settings.FRONTEND_URL_BASE}'


def auth_request(request):
    """Simple 'auth' endpoint used to determine if the user is authenticated.

    Useful for (for example) redirecting authentication requests through django's permission framework.
    """
    if (
        not request.user
        or not request.user.is_authenticated
        or not request.user.is_active
    ):
        # This is very unlikely to be reached, as the middleware stack should intercept unauthenticated requests
        return HttpResponse(status=403)  # pragma: no cover

    # User is authenticated and active
    return HttpResponse(status=200)
