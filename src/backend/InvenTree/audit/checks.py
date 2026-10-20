"""System checks for the audit app."""

from django.conf import settings
from django.core import checks

AUDIT_MIDDLEWARE = 'audit.middleware.InvenTreeAuditlogMiddleware'


@checks.register()
def check_audit_middleware(app_configs, **kwargs):
    """Warn if the audit middleware is missing.

    MIDDLEWARE can be overridden from the config file - without the audit middleware,
    audit entries are still created but the actor and remote address are not recorded.
    """
    if AUDIT_MIDDLEWARE in settings.MIDDLEWARE:
        return []

    return [
        checks.Warning(
            f"'{AUDIT_MIDDLEWARE}' is not present in MIDDLEWARE",
            hint='Audit log entries will not record the user who made each change',
            id='inventree.audit.W001',
        )
    ]
