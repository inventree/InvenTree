"""Utility helpers for tenant database management."""

from __future__ import annotations
from typing import List


import ipaddress
import logging
import re
from typing import List, Optional
import psycopg2

from django.conf import settings
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError

logger = logging.getLogger("inventree")


_EXCLUDED_DATABASES = {"template0", "template1"}


def get_dbfilter_pattern() -> str:
    """Return the configured dbfilter pattern (may be empty)."""

    return getattr(settings, "TENANT_DBFILTER", "") or ""


def _normalize_host(host: str) -> str:
    host = host.lower()
    if ":" in host:
        host, _ = host.split(":", 1)
    return host


logger = logging.getLogger(__name__)


def get_available_databases() -> List[str]:
    """Return the list of accessible PostgreSQL databases."""
    db_settings = connection.settings_dict
    default_name = db_settings.get("NAME")

    # Only works for PostgreSQL
    if db_settings.get("ENGINE") != "django.db.backends.postgresql":
        return [default_name] if default_name else []

    try:
        conn = psycopg2.connect(
            dbname="postgres",  # connect to system catalog
            user=db_settings.get("USER"),
            password=db_settings.get("PASSWORD"),
            host=db_settings.get("HOST"),
            port=db_settings.get("PORT", 5432),
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT datname FROM pg_database WHERE datallowconn = true AND datistemplate = false;"
        )
        databases = [
            row[0]
            for row in cur.fetchall()
            if row[0] not in ("postgres", "template0", "template1")
        ]
        cur.close()
        conn.close()

        logger.debug("🧩 PostgreSQL databases detected: %s", databases)
        return sorted(dict.fromkeys(databases))
    except Exception as exc:
        logger.warning("Unable to list databases: %s", exc)
        return [default_name] if default_name else []


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
