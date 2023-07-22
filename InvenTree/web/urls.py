"""URLs for web app."""
from django.conf import settings
from django.shortcuts import redirect
from django.urls import path, re_path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView


class RedirectAssetView(TemplateView):
    """View to redirect to static asset."""

    def get(self, request, *args, **kwargs):
        """Redirect to static asset."""
        return redirect(
            f"{settings.STATIC_URL}web/assets/{kwargs['path']}", permanent=True
        )


spa_view = ensure_csrf_cookie(TemplateView.as_view(template_name="web/index.html"))


urlpatterns = [
    path("assets/<path:path>", RedirectAssetView.as_view()),
    re_path(r"^(?P<path>.*)/$", spa_view),
    path("set-password?uid=<uid>&token=<token>", spa_view, name="password_reset_confirm"),
    path("", spa_view),
]
