"""Hardening helpers for report / label template rendering.

Templates are considered trusted (see the threat model), but rendering is
restricted as defence-in-depth: while a template renders, tables holding
credentials, sessions, tokens, or outbound mail cannot be queried - neither via
``filter_db_model`` nor by relation traversal.

Note: this operates on whole tables. It cannot hide individual rows or
columns of tables that are legitimately needed by reports.
"""

import re
from contextlib import ExitStack, contextmanager

from django.apps import apps
from django.core.exceptions import PermissionDenied
from django.db import connections

# Models which may never be accessed while rendering a template
BLOCKED_MODELS = [
    'sessions.session',
    'common.emailmessage',
    'common.emailthread',
    'common.webhookendpoint',
    'common.webhookmessage',
    'users.apitoken',
    'authtoken.token',
    'socialaccount.socialtoken',
    'socialaccount.socialapp',
    'socialaccount.socialaccount',
    'oauth2_provider.accesstoken',
    'oauth2_provider.refreshtoken',
    'oauth2_provider.grant',
    'oauth2_provider.idtoken',
    'oauth2_provider.application',
    'mfa.authenticator',
    'usersessions.usersession',
    'account.emailaddress',
    'account.emailconfirmation',
]

# Apps for which every model is blocked
BLOCKED_APPS = ['sessions', 'socialaccount', 'oauth2_provider', 'mfa', 'usersessions']

_WORD = re.compile(r'\w+')


class ReportAccessDenied(PermissionDenied):
    """Raised when a template attempts to access restricted data."""


def _blocked_model_set() -> set:
    blocked = set()

    for label in BLOCKED_MODELS:
        try:
            blocked.add(apps.get_model(label))
        except (LookupError, ValueError):
            continue

    for app_label in BLOCKED_APPS:
        try:
            blocked.update(apps.get_app_config(app_label).get_models())
        except LookupError:
            continue

    return blocked


def blocked_tables() -> set:
    """Return the set of lowercase DB table names which are blocked."""
    tables = set()

    for model in _blocked_model_set():
        tables.add(model._meta.db_table.lower())

        # Auto-created M2M tables
        for field in model._meta.local_many_to_many:
            tables.add(field.m2m_db_table().lower())

    return tables


def is_model_blocked(model) -> bool:
    """Check if the provided model class is blocked for template access."""
    return model in _blocked_model_set()


def _guard(tables: set):
    def wrapper(execute, sql, params, many, context):
        if tables.intersection(w.lower() for w in _WORD.findall(sql)):
            raise ReportAccessDenied('Access to this data is not allowed in templates')

        return execute(sql, params, many, context)

    return wrapper


@contextmanager
def restricted_db_access():
    """Context manager: prevent database access to restricted tables."""
    guard = _guard(blocked_tables())

    with ExitStack() as stack:
        for conn in connections.all():
            stack.enter_context(conn.execute_wrapper(guard))
        yield
