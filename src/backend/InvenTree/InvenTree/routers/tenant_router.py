"""Database router that assigns ORM activity to the active tenant database."""

from __future__ import annotations

from copy import deepcopy
from typing import Optional

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connections

from InvenTree.InvenTree.tenant import get_current_database


class TenantDatabaseRouter:
    """Route all ORM operations to the tenant database when available."""

    def _get_tenant_alias(self) -> Optional[str]:
        database_name = get_current_database()

        if not database_name:
            return None

        if database_name in settings.DATABASES:
            return database_name

        alias = f"tenant_{database_name}"

        if alias in settings.DATABASES:
            return alias

        default_config = settings.DATABASES.get(DEFAULT_DB_ALIAS)

        if not default_config:
            return None

        new_config = deepcopy(default_config)
        new_config['NAME'] = database_name

        settings.DATABASES[alias] = new_config
        connections.databases[alias] = new_config

        return alias

    def db_for_read(self, model, **hints):
        return self._get_tenant_alias()

    def db_for_write(self, model, **hints):
        return self._get_tenant_alias()

    def allow_relation(self, obj1, obj2, **hints):
        tenant_alias = self._get_tenant_alias()

        if tenant_alias is None:
            return None

        if obj1._state.db == tenant_alias or obj2._state.db == tenant_alias:
            return True

        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        tenant_alias = self._get_tenant_alias()

        if tenant_alias is None:
            return None

        return db == tenant_alias
