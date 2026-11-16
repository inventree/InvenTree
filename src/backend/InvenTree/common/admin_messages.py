"""Staff-only system messages, displayed in the admin center.

Each message describes the outcome of a single system check. Messages are
generated on demand (they are not stored in the database), and are exposed
via the read-only /api/system/messages/ endpoint.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

from django.conf import settings
from django.utils.translation import gettext_lazy as _

import structlog

from common.settings import get_global_setting

logger = structlog.get_logger('inventree')


class AdminMessageClassifier(StrEnum):
    """Severity classifier for an admin message."""

    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'
    SUCCESS = 'success'


# Ordering used when sorting messages (most severe first)
CLASSIFIER_RANK = {
    AdminMessageClassifier.ERROR: 0,
    AdminMessageClassifier.WARNING: 1,
    AdminMessageClassifier.INFO: 2,
    AdminMessageClassifier.SUCCESS: 3,
}


@dataclass
class AdminMessage:
    """A single staff-facing system message.

    Attributes:
        key: Unique identifier for the message (e.g. 'worker')
        title: Short, human readable title
        message: Detailed message text
        classifier: Severity of the message
        code: Optional InvenTree error code (e.g. 'INVE-W5'), used to link to documentation
        plugin: Slug of the plugin which provided this message (None for core messages)
    """

    key: str
    title: str
    message: str
    classifier: AdminMessageClassifier
    code: Optional[str] = None
    plugin: Optional[str] = None


def _check(
    key: str,
    title: str,
    message: str,
    condition: bool,
    code: Optional[str] = None,
    classifier: AdminMessageClassifier = AdminMessageClassifier.WARNING,
) -> AdminMessage:
    """Construct a message for a simple pass/fail system check.

    Arguments:
        key: Unique message key
        title: Message title
        message: Message text to display if the check fails
        condition: True if the check has *failed* (i.e. the issue is present)
        code: Optional error code
        classifier: Classifier to use if the check fails
    """
    if condition:
        return AdminMessage(
            key=key, title=title, message=message, classifier=classifier, code=code
        )

    return AdminMessage(
        key=key,
        title=title,
        message=_('No issues detected'),
        classifier=AdminMessageClassifier.SUCCESS,
        code=code,
    )


def _pending_migrations() -> int:
    """Return the number of pending database migrations (as recorded by the background worker)."""
    try:
        return int(get_global_setting('_PENDING_MIGRATIONS', 0) or 0)
    except (TypeError, ValueError):
        return 0


def get_core_admin_messages() -> list[AdminMessage]:
    """Return the set of core InvenTree system messages."""
    # Imported here to avoid circular imports at app load
    from InvenTree.helpers_email import is_email_configured
    from InvenTree.status import is_worker_running

    return [
        _check(
            'debug',
            _('Debug Mode'),
            _('The server is running in debug mode.'),
            bool(settings.DEBUG),
            code='INVE-W4',
        ),
        _check(
            'worker',
            _('Background Worker'),
            _('The background worker process is not running.'),
            not is_worker_running(),
            code='INVE-W5',
        ),
        _check(
            'restart',
            _('Server Restart'),
            _('The server requires a restart to apply changes.'),
            bool(get_global_setting('SERVER_RESTART_REQUIRED', False, cache=False)),
            code='INVE-W6',
        ),
        _check(
            'email',
            _('Email settings'),
            _('Email settings not configured.'),
            not is_email_configured(),
            code='INVE-W7',
        ),
        _check(
            'migrations',
            _('Database Migrations'),
            _('There are pending database migrations.'),
            _pending_migrations() > 0,
            code='INVE-W8',
        ),
        _check(
            'cors',
            _('CORS Settings'),
            _('CORS is set to allow all origins.'),
            bool(settings.CORS_ALLOW_ALL_ORIGINS),
            code='INVE-W16',
        ),
        _check(
            'basic_auth',
            _('Basic Authentication'),
            _('Basic (username:password) authentication is enabled for the API.'),
            bool(settings.BASIC_AUTH_ENABLED),
            code='INVE-W18',
        ),
    ]


def get_plugin_admin_messages() -> list[AdminMessage]:
    """Return system messages provided by plugins.

    PLACEHOLDER: There is not yet a plugin mixin for providing admin messages.

    The intended design is a dedicated mixin (e.g. 'AdminMessageMixin') with a
    method returning a list of AdminMessage objects. Each returned message
    should be tagged with the providing plugin's slug (AdminMessage.plugin),
    and have its key namespaced (e.g. '<slug>.<key>') to avoid collisions
    with core messages. Any exception raised by a plugin must be caught and
    logged here, so that a faulty plugin cannot break the endpoint.
    """
    return []


def get_admin_messages() -> list[AdminMessage]:
    """Return all admin messages (core and plugin), sorted most severe first."""
    messages = get_core_admin_messages() + get_plugin_admin_messages()

    # Stable sort - preserves definition order within each classifier
    return sorted(messages, key=lambda msg: CLASSIFIER_RANK[msg.classifier])
