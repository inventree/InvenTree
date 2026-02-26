"""Various Views which provide extra functionality over base Django Views.

In particular these views provide base functionality for rendering Django forms
as JSON objects and passing them to modal forms (using jQuery / bootstrap).
"""

from django.http import HttpResponse


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
