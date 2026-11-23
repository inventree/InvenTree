"""Generic models which provide extra functionality over base Django model types."""

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.translation import gettext_lazy as _

import structlog
from django_q.models import Task
from django_q.signals import post_execute
from error_report.models import Error

import InvenTree.helpers_model

# legacy imports
from generic.models.base import (  # noqa: F401
    InvenTreeMetadataModel,
    InvenTreeModel,
    InvenTreeTree,
)
from generic.models.modelmixins import (  # noqa: F401
    InvenTreeAttachmentMixin,
    InvenTreeAuditMixin,
    InvenTreeBarcodeMixin,
    InvenTreeImageMixin,
    InvenTreeNoteMixin,
    InvenTreeParameterMixin,
    InvenTreeTagsMixin,
)
from generic.models.modelmixins import (
    InvenTreeMetadataMixin as MetadataMixin,  # noqa: F401
)
from generic.models.modelmixins import (
    InvenTreePathStringMixin as PathStringMixin,  # noqa: F401
)
from generic.models.modelmixins import (
    InvenTreePluginValidationMixin as PluginValidationMixin,  # noqa: F401
)
from generic.models.modelmixins import (
    InvenTreeReferenceIndexingMixin as ReferenceIndexingMixin,  # noqa: F401
)

logger = structlog.get_logger('inventree')


def notify_staff_users_of_error(instance, label: str, context: dict):
    """Helper function to notify staff users of an error."""
    import common.models
    import common.notifications
    from plugin.builtin.integration.core_notifications import InvenTreeUINotifications

    try:
        # Get all staff users
        staff_users = get_user_model().objects.filter(is_active=True, is_staff=True)

        target_users = []

        # Send a notification to each staff user (unless they have disabled error notifications)
        for user in staff_users:
            if common.models.InvenTreeUserSetting.get_setting(
                'NOTIFICATION_ERROR_REPORT', True, user=user
            ):
                target_users.append(user)

        if len(target_users) > 0:
            common.notifications.trigger_notification(
                instance,
                label,
                context=context,
                targets=target_users,
                delivery_methods={InvenTreeUINotifications},
            )

    except Exception as exc:
        # We do not want to throw an exception while reporting an exception!
        logger.error(exc)


def _notify_task_failure(func: str, task_id: str, attempt_count: int, result) -> None:
    """Create a new Error object for a permanently-failed background task.

    This will, in turn, trigger a notification to staff users via the Error post_save signal.
    """
    from InvenTree.exceptions import log_error

    message = f"Task '{func} ({task_id})' failed after {attempt_count} attempt{'s' if attempt_count != 1 else ''}"

    logger.error(message)

    log_error(
        'task_failure',
        scope='worker',
        error_name='Task Failure',
        error_info=message,
        error_data=str(result) if result else '',
    )


@receiver(post_save, sender=Task, dispatch_uid='failure_post_save_notification')
def after_failed_task(sender, instance: Task, created: bool, **kwargs):
    """Callback when a new task failure log is generated."""
    from django.conf import settings

    max_attempts = int(settings.Q_CLUSTER.get('max_attempts', 5))
    n = instance.attempt_count

    # Only notify once the maximum number of attempts has been reached
    if not instance.success and n >= max_attempts:
        _notify_task_failure(instance.func, instance.pk, n, instance.result)


@receiver(post_execute, dispatch_uid='failure_post_execute_notification')
def after_single_shot_task_failure(sender, task: dict, **kwargs):
    """Callback when a background task finishes executing.

    A task offloaded with offload_task(..., retry=False) is marked with the
    'ack_failure' option, which causes the broker to drop it after a single failed
    attempt (see InvenTree.tasks.offload_task) - its attempt_count will never reach
    Q_CLUSTER['max_attempts'], so after_failed_task()'s post_save-based check would
    otherwise never fire a notification for it. This uses django-q2's post_execute
    signal instead, which (unlike the saved Task record) still carries the
    'ack_failure' flag, to notify immediately on that task's one and only attempt.
    """
    from django.conf import settings

    if task.get('success') or not task.get('ack_failure'):
        return

    max_attempts = int(settings.Q_CLUSTER.get('max_attempts', 5))

    if max_attempts <= 1:
        # after_failed_task() already handles this case via its own post_save signal -
        # avoid notifying twice
        return

    from django_q.utils import get_func_repr

    _notify_task_failure(
        get_func_repr(task.get('func')), task.get('id'), 1, task.get('result')
    )


@receiver(post_save, sender=Error, dispatch_uid='error_post_save_notification')
def after_error_logged(sender, instance: Error, created: bool, **kwargs):
    """Callback when a server error is logged.

    - Send a UI notification to all users with staff status
    """
    if created:
        try:
            url = InvenTree.helpers_model.construct_absolute_url(
                reverse(
                    'admin:error_report_error_change', kwargs={'object_id': instance.pk}
                )
            )
        except NoReverseMatch:
            url = ''

        notify_staff_users_of_error(
            instance,
            'inventree.error_log',
            {
                'error': instance,
                'name': _('Server Error'),
                'message': _('An error has been logged by the server.'),
                'link': url,
            },
        )
