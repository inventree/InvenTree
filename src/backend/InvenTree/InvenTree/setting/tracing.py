"""Start-up configuration options for InvenTree tracing integrations."""

import structlog

from InvenTree.config import get_boolean_setting, get_setting
from InvenTree.tracing import setup_instruments, setup_tracing

logger = structlog.get_logger('inventree')


def configure_tracing(db_engine: str, enabled: bool, tags: dict) -> dict:
    """Configure tracing integrations for InvenTree.

    Arguments:
        db_engine: The database engine being used
        enabled: Whether tracing is enabled
        tags: A dictionary of tags to be included in tracing spans, with keys prefixed by
    """
    endpoint = get_setting('INVENTREE_TRACING_ENDPOINT', 'tracing.endpoint', None)
    headers = (
        get_setting('INVENTREE_TRACING_HEADERS', 'tracing.headers', None, typecast=dict)
        or {}
    )

    if enabled and endpoint:
        logger.info('Tracing enabled with endpoint: %s', endpoint)

    TRACING_DETAILS = {
        'endpoint': endpoint,
        'headers': headers,
        'resources_input': {
            **{'inventree.env.' + k: v for k, v in tags.items()},
            **get_setting(
                'INVENTREE_TRACING_RESOURCES',
                'tracing.resources',
                default_value=None,
                typecast=dict,
            ),
        },
        'console': get_boolean_setting(
            'INVENTREE_TRACING_CONSOLE', 'tracing.console', False
        ),
        'auth': get_setting(
            'INVENTREE_TRACING_AUTH', 'tracing.auth', default_value=None, typecast=dict
        ),
        'is_http': get_setting('INVENTREE_TRACING_IS_HTTP', 'tracing.is_http', True),
        'append_http': get_boolean_setting(
            'INVENTREE_TRACING_APPEND_HTTP', 'tracing.append_http', True
        ),
    }

    if not enabled:
        return None

    if endpoint:
        setup_tracing(**TRACING_DETAILS)
        setup_instruments(db_engine)
    else:
        logger.warning('OpenTelemetry tracing not enabled because endpoint is not set')

    return TRACING_DETAILS
