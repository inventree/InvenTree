"""Thread / async safe tenant context helpers."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Optional

_TENANT_SUBDOMAIN: ContextVar[Optional[str]] = ContextVar(
    "inventree_tenant_subdomain", default=None
)
_TENANT_DATABASE: ContextVar[Optional[str]] = ContextVar(
    "inventree_tenant_database", default=None
)


def set_current_subdomain(subdomain: Optional[str]) -> None:
    """Store the current request subdomain in context."""

    _TENANT_SUBDOMAIN.set(subdomain)


def get_current_subdomain() -> Optional[str]:
    """Return the current request subdomain if set."""

    return _TENANT_SUBDOMAIN.get()


def set_current_database(database: Optional[str]) -> None:
    """Store the current tenant database name in context."""

    _TENANT_DATABASE.set(database)


def get_current_database() -> Optional[str]:
    """Return the current tenant database if set."""

    return _TENANT_DATABASE.get()


def clear_tenant_context() -> None:
    """Reset tenant information at the end of a request."""

    _TENANT_SUBDOMAIN.set(None)
    _TENANT_DATABASE.set(None)
