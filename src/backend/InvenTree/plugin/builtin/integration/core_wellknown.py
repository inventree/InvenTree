"""Base plugin which defines the built-in well-known entries."""

from django.http import HttpRequest, JsonResponse
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

import InvenTree.helpers
from plugin import InvenTreePlugin
from plugin.mixins import UrlsMixin, WellKnownMixin


class InvenTreeWellKnown(WellKnownMixin, UrlsMixin, InvenTreePlugin):
    """Plugin which provides built-in well-known URLs."""

    NAME = 'InvenTreeWellKnown'
    SLUG = 'inventree-well-known'
    TITLE = _('InvenTree Well-Known URLs')
    DESCRIPTION = _('Built-in well-known URLs for InvenTree')
    AUTHOR = _('InvenTree contributors')
    VERSION = '1.0.0'

    def get_well_known_urls(
        self, request: 'HttpRequest | None' = None
    ) -> list[tuple[str, str]]:
        """Return all built-in well-known entries."""
        data = []

        # See https://www.w3.org/TR/passkey-endpoints/
        data.append(('passkey-endpoints', reverse(f'plugin:{self.slug}:passkey')))

        # placeholder for more
        return data

    @require_http_methods(['GET'])
    def view_passkey(self, request, *args, **kwargs):
        """Return the passkey well-known entry."""
        passkey_web = request.build_absolute_uri(
            InvenTree.helpers.pui_url('/settings/user/security')
        )
        return JsonResponse({'enroll': passkey_web, 'manage': passkey_web})

    def setup_urls(self):
        """Urls that are exposed by this plugin."""
        return [path('passkey/', self.view_passkey, name='passkey')]
