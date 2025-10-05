"""Utility helpers for tenant database management."""

from __future__ import annotations

import ipaddress
import logging
import re
from typing import List, Optional

from django.conf import settings
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError

logger = logging.getLogger("inventree")


_EXCLUDED_DATABASES = {"template0", "template1"}


def get_dbfilter_pattern() -> str:
    """Return the configured dbfilter pattern (may be empty)."""

    return getattr(settings, "TENANT_DBFILTER", "") or ""


def get_available_databases() -> List[str]:
    """Return the list of accessible databases on the PostgreSQL server."""

    introspection = getattr(connection, "introspection", None)
    default_name = connection.settings_dict.get("NAME")

    if introspection is None or not hasattr(introspection, "get_database_list"):
        return [default_name] if default_name else []

    try:
        databases = introspection.get_database_list()
    except (OperationalError, ProgrammingError) as exc:  # pragma: no cover - depends on DB perms
        logger.warning("Unable to list databases via introspection: %s", exc)
        return [default_name] if default_name else []

    filtered = []
    for name in databases:
        if not name:
            continue
        if name in _EXCLUDED_DATABASES:
            continue
        filtered.append(name)

    if default_name and default_name not in filtered:
        filtered.append(default_name)

    return sorted(dict.fromkeys(filtered))


def _normalize_host(host: str) -> str:
    host = host.lower()
    if ":" in host:
        host, _ = host.split(":", 1)
    return host


def extract_subdomain(host: str) -> Optional[str]:
    """Extract the leading subdomain from a host string."""

    normalized = _normalize_host(host)

    try:
        ipaddress.ip_address(normalized)
        return None
    except ValueError:
        pass

    labels = [label for label in normalized.split(".") if label]

    if len(labels) < 3:
        return None

    return labels[0]


def get_database_for_subdomain(subdomain: Optional[str]) -> Optional[str]:
    """Return the database name mapped to the provided subdomain."""

    if not subdomain:
        return None

    pattern = get_dbfilter_pattern()
    databases = get_available_databases()

    if not databases:
        return None

    if pattern:
        regex_pattern = pattern
        if "%s" in pattern:
            regex_pattern = pattern.replace("%s", re.escape(subdomain))

        matches = [db for db in databases if re.fullmatch(regex_pattern, db)]

        for candidate in matches:
            if candidate == subdomain:
                return candidate

        if matches:
            return matches[0]
    else:
        if subdomain in databases:
            return subdomain

    return None
