"""The audit app provides a read-only change history for InvenTree models.

Built on top of django-auditlog, with an InvenTree specific LogEntry model
(see audit.models.AuditLogEntry) which links entries to a "parent" object.
"""
