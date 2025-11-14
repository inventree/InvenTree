"""Code for managing email functionality in InvenTree."""

from typing import Optional

from django.conf import settings

import structlog
from allauth.account.models import EmailAddress

import InvenTree.ready
from common.models import Priority, issue_mail

logger = structlog.get_logger('inventree')


def is_email_configured() -> bool:
    """Check if email backend is configured.

    Fails on tests nominally, if no bypassed via settings.TESTING_BYPASS_MAILCHECK.

    NOTE: This does not check if the configuration is valid!
    """
    configured = True
    testing = settings.TESTING

    if InvenTree.ready.isInTestMode():
        return settings.TESTING_BYPASS_MAILCHECK

    if InvenTree.ready.isImportingData():
        return False

    # Might be using a different INTERNAL_EMAIL_BACKEND
    if settings.INTERNAL_EMAIL_BACKEND != 'django.core.mail.backends.smtp.EmailBackend':
        # If we are using a different email backend, we don't need to check
        # the SMTP settings
        return True

    if not settings.EMAIL_HOST:
        configured = False

        # Display warning unless in test mode
        if not testing:  # pragma: no cover
            logger.debug('INVE-W7: EMAIL_HOST is not configured')

    # Display warning unless in test mode
    if not settings.EMAIL_HOST_USER and not testing:  # pragma: no cover
        logger.debug('INVE-W7: EMAIL_HOST_USER is not configured')

    # Display warning unless in test mode
    if not settings.EMAIL_HOST_PASSWORD and testing:  # pragma: no cover
        logger.debug('INVE-W7: EMAIL_HOST_PASSWORD is not configured')

    # Email sender must be configured
    if not settings.DEFAULT_FROM_EMAIL:
        configured = False

        if not testing:  # pragma: no cover
            logger.debug('DEFAULT_FROM_EMAIL is not configured')

    return configured


def send_email(
    subject: str,
    body: str,
    recipients: str | list,
    from_email: Optional[str] = None,
    html_message=None,
    prio: Priority = Priority.NORMAL,
    headers: Optional[dict] = None,
) -> tuple[bool, Optional[str]]:
    """Send an email with the specified subject and body, to the specified recipients list."""
    if isinstance(recipients, str):
        recipients = [recipients]

    import InvenTree.ready

    if InvenTree.ready.isImportingData():
        # If we are importing data, don't send emails
        return False, 'Data import in progress'

    if not is_email_configured() and not settings.TESTING:
        # Email is not configured / enabled
        logger.info('INVE-W7: Email will not be send, no mail server configured')
        return False, 'INVE-W7: Email server not configured'

    # If a *from_email* is not specified, ensure that the default is set
    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL

        # If we still don't have a valid from_email, then we can't send emails
        if not from_email:
            if settings.TESTING:
                from_email = 'test@test.inventree.org'
            else:
                logger.error(
                    'INVE-W7: send_email failed: DEFAULT_FROM_EMAIL not specified'
                )
                return False, 'INVE-W7: no from_email or DEFAULT_FROM_EMAIL specified'

    InvenTree.tasks.offload_task(
        issue_mail,
        subject=subject,
        body=body,
        from_email=from_email,
        recipients=recipients,
        fail_silently=False,
        html_message=html_message,
        prio=prio,
        headers=headers,
        group='notification',
    )
    return True, None


def get_email_for_user(user) -> Optional[str]:
    """Find an email address for the specified user."""
    # First check if the user has an associated email address
    if user.email:
        return user.email

    # Otherwise, find first matching email
    # Priority is given to primary or verified email addresses
    if (
        email := EmailAddress.objects.filter(user=user)
        .order_by('-primary', '-verified')
        .first()
    ):
        return email.email
