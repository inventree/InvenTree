"""Signal receivers for the audit app."""

from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from auditlog.signals import pre_log

from audit.models import DEFERRED_LOG_ATTR


@receiver(pre_log, dispatch_uid='inventree_audit_pre_log')
def check_audit_enabled(sender, instance, action, **kwargs):
    """Skip writing audit entries if the audit log is disabled via global setting.

    Returning False from a pre_log receiver prevents the entry being created.
    """
    from common.settings import get_global_setting

    # create=False: never write to the settings table from within the audit hook
    if not get_global_setting('AUDIT_LOG_ENABLED', True, create=False):
        return False

    return None


@receiver(pre_save, dispatch_uid='inventree_audit_clear_deferred_log')
def clear_deferred_log(sender, instance, **kwargs):
    """Discard any deferred entry left over from a previous (failed) save of this instance.

    Connected before the auditlog receivers (see AuditConfig.ready), so runs first.
    """
    instance.__dict__.pop(DEFERRED_LOG_ATTR, None)


@receiver(post_save, dispatch_uid='inventree_audit_resolve_deferred_log')
def resolve_deferred_log(sender, instance, created, **kwargs):
    """Write a deferred audit entry, with query expression values resolved from the database."""
    from auditlog.diff import get_field_value

    from audit.models import AuditLogEntry

    if not (pending := instance.__dict__.pop(DEFERRED_LOG_ATTR, None)):
        return

    saved = sender._base_manager.filter(pk=instance.pk).first()

    if saved is None:  # pragma: no cover
        return

    log_kwargs = pending['kwargs']
    changes = dict(log_kwargs['changes'])

    for name in pending['fields']:
        old = changes[name][0]
        new = get_field_value(
            saved,
            sender._meta.get_field(name),
            use_json_for_changes=settings.AUDITLOG_STORE_JSON_CHANGES,
        )
        changes[name] = [old, new]

    AuditLogEntry.objects.log_create(
        instance,
        force_log=pending['force_log'],
        _audit_resolved=True,
        **{**log_kwargs, 'changes': changes},
    )
