"""Middleware for resolving the active tenant database."""

from __future__ import annotations

from typing import Optional

from django.conf import settings
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

from InvenTree.InvenTree.tenant import (
    clear_tenant_context,
    extract_subdomain,
    get_available_databases,
    get_database_for_subdomain,
    get_dbfilter_pattern,
    set_current_database,
    set_current_subdomain,
)

_SELECT_DB_PATH = "/select-db/"


class TenantMiddleware(MiddlewareMixin):
    """Determine the database that should be used for the current request."""

    def _should_skip_redirect(self, request) -> bool:
        path = request.path
        if path.startswith(settings.STATIC_URL or "/static/"):
            return True
        if path.startswith(settings.MEDIA_URL or "/media/"):
            return True
        if path.startswith(_SELECT_DB_PATH):
            return True
        return False

    def _handle_subdomain(self, request, subdomain: Optional[str]) -> Optional[str]:
        dbfilter = get_dbfilter_pattern()

        if not dbfilter:
            return None

        database = get_database_for_subdomain(subdomain)

        if database:
            request.session['tenant_database'] = database

        return database

    def _handle_session_selection(self, request) -> Optional[str]:
        selected = request.session.get('tenant_database')

        if selected:
            return selected

        databases = get_available_databases()

        if not databases:
            return None

        if len(databases) == 1:
            selected = databases[0]
            request.session['tenant_database'] = selected
            return selected

        request.available_databases = databases

        if self._should_skip_redirect(request):
            return None

        return None

    def process_request(self, request):
        subdomain = extract_subdomain(request.get_host())
        request.tenant_subdomain = subdomain
        set_current_subdomain(subdomain)

        dbfilter_enabled = bool(get_dbfilter_pattern())

        database = self._handle_subdomain(request, subdomain)

        if database is None and not dbfilter_enabled:
            database = self._handle_session_selection(request)

            if database is None:
                databases = getattr(request, 'available_databases', None)
                if databases and len(databases) > 1 and not self._should_skip_redirect(request):
                    return redirect(_SELECT_DB_PATH)

        if database:
            request.tenant_database = database
            set_current_database(database)
        elif not dbfilter_enabled:
            request.tenant_database = request.session.get('tenant_database')
            if request.tenant_database:
                set_current_database(request.tenant_database)
        else:
            request.tenant_database = None

    def process_response(self, request, response):
        clear_tenant_context()
        return response

    def process_exception(self, request, exception):  # pragma: no cover - defensive
        clear_tenant_context()
        return None
