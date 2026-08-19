"""URLs for web app."""

from django.conf import settings
from django.urls import include, path, re_path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView

spa_view = ensure_csrf_cookie(TemplateView.as_view(template_name='web/index.html'))

urlpatterns = [
    path(
        f'{settings.FRONTEND_URL_BASE}/',
        include([
            path(
                'set-password?uid=<uid>&token=<token>',
                spa_view,
                name='password_reset_confirm',
            ),
            re_path('.*', spa_view, name='web-wildcard'),
        ]),
    ),
    path(settings.FRONTEND_URL_BASE, spa_view, name='web'),
]
