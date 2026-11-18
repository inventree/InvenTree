"""Admin site configuration for the audit app."""

from django.contrib import admin

# Ensure the upstream admin class has been registered, so that it can be replaced below
import auditlog.admin
from auditlog.filters import CIDFilter, ResourceTypeFilter

from audit.models import AuditLogEntry

if admin.site.is_registered(AuditLogEntry):
    admin.site.unregister(AuditLogEntry)


@admin.register(AuditLogEntry)
class AuditLogEntryAdmin(auditlog.admin.LogEntryAdmin):
    """Admin class for the AuditLogEntry model.

    Extends the (read-only) upstream LogEntry admin, adding:
    - Filtering by the user who made the change
    """

    list_filter = [
        'action',
        # Only list users which have recorded entries
        ('actor', admin.RelatedOnlyFieldListFilter),
        ResourceTypeFilter,
        CIDFilter,
    ]
