"""Signal receivers for the audit app."""

from django.dispatch import receiver

from auditlog.signals import pre_log


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
