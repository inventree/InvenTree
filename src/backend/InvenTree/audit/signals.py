"""Signal receivers for the audit app."""

from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from auditlog.signals import pre_log
from django_q.signals import post_execute_in_worker, pre_execute

import audit.context
from audit.models import DEFERRED_LOG_ATTR


@receiver(pre_log, dispatch_uid='inventree_audit_pre_log')
def check_audit_enabled(sender, instance, action, **kwargs):
    """Skip writing audit entries if the audit log is disabled via global setting.

    - Instances can opt out of being recorded (should_audit)
    - Instances can be recorded even if the audit log is disabled (audit_always)

    Returning False from a pre_log receiver prevents the entry being created.
    """
    from common.settings import get_global_setting

    should_audit = getattr(instance, 'should_audit', None)

    if callable(should_audit) and not should_audit():
        return False

    audit_always = getattr(instance, 'audit_always', None)

    if callable(audit_always) and audit_always():
        return None

    # create=False: never write to the settings table from within the audit hook
    if not get_global_setting('AUDIT_LOG_ENABLED', True, create=False):
        return False

    return None


def recorded_field_value(model, instance, field_name: str):
    """Return the value of a field, in the form recorded by auditlog.

    Mirrors the conversion applied by auditlog.diff.model_instance_diff(),
    so that deferred entries are identical to those recorded directly.
    """
    from django.utils.encoding import smart_str

    from auditlog.diff import get_field_value, get_mask_function, is_primitive
    from auditlog.registry import auditlog

    use_json = settings.AUDITLOG_STORE_JSON_CHANGES
    value = get_field_value(instance, model._meta.get_field(field_name), use_json)

    model_fields = auditlog.get_model_fields(model)

    if field_name in model_fields['mask_fields']:
        mask_func = get_mask_function(model_fields.get('mask_callable'))
        return mask_func(smart_str(value))

    if not use_json or not is_primitive(value):
        return smart_str(value)

    return value


@receiver(pre_save, dispatch_uid='inventree_audit_clear_deferred_log')
def clear_deferred_log(sender, instance, **kwargs):
    """Discard any deferred entry left over from a previous (failed) save of this instance.

    Connected before the auditlog receivers (see AuditConfig.ready), so runs first.
    """
    instance.__dict__.pop(DEFERRED_LOG_ATTR, None)


@receiver(post_save, dispatch_uid='inventree_audit_resolve_deferred_log')
def resolve_deferred_log(sender, instance, created, **kwargs):
    """Write a deferred audit entry, with query expression values resolved from the database."""
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
        new = recorded_field_value(sender, saved, name)
        changes[name] = [old, new]

    AuditLogEntry.objects.log_create(
        instance,
        force_log=pending['force_log'],
        _audit_resolved=True,
        **{**log_kwargs, 'changes': changes},
    )


@receiver(pre_execute, dispatch_uid='inventree_audit_pre_execute')
def begin_worker_task(sender, func, task, **kwargs):
    """Tag audit entries created by a background worker task with the task name."""
    audit.context.begin_worker_task(task.get('func') or func)


@receiver(post_execute_in_worker, dispatch_uid='inventree_audit_post_execute')
def end_worker_task(sender, func, task, **kwargs):
    """Clear the audit context once a background worker task has finished."""
    audit.context.end_worker_task()
