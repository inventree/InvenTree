"""Configuration options for InvenTree external cache."""

import socket
import threading
from typing import Any

from django.db.utils import OperationalError, ProgrammingError

import structlog

import InvenTree.config
import InvenTree.ready

logger = structlog.get_logger('inventree')

# Thread-local cache for caching data against the request object
thread_data = threading.local()


def cache_setting(name, default=None, **kwargs):
    """Return the value of a particular cache setting.

    Arguments:
        name: The name of the cache setting
        default: The default value to return if the setting is not found
        kwargs: Additional arguments to pass to the cache setting request
    """
    return InvenTree.config.get_setting(
        f'INVENTREE_CACHE_{name.upper()}', f'cache.{name.lower()}', default, **kwargs
    )


def cache_host():
    """Return the cache host address."""
    return cache_setting('host', None)


def cache_port() -> int:
    """Return the cache port."""
    return cache_setting('port', '6379', typecast=int)


def cache_password():
    """Return the cache password."""
    return cache_setting('password', None)


def cache_user():
    """Return the cash username."""
    return cache_setting('user', None)


def is_global_cache_enabled() -> bool:
    """Check if the global cache is enabled.

    - Test if the user has enabled and configured global cache
    - Test if it is appropriate to enable global cache based on the current operation.
    """
    host = cache_host()

    # Test if cache is enabled
    # If the cache host is set, then the "default" action is to enable the cache
    if not cache_setting('enabled', host is not None, typecast=bool):
        return False

    # Test if the cache is configured
    if not cache_host():
        logger.warning('Global cache is enabled, but no cache host is configured!')
        return False

    # The cache should not be used during certain operations
    if not InvenTree.ready.canAppAccessDatabase(
        allow_test=False, allow_plugins=False, allow_shell=True
    ):
        logger.info('Global cache bypassed for this operation')
        return False

    logger.info('Global cache enabled')

    return True


def get_cache_config(global_cache: bool) -> dict:
    """Return the cache configuration options.

    Args:
      global_cache: True if the global cache is enabled.

    Returns:
        A dictionary containing the cache configuration options.
    """
    if global_cache:
        # Build Redis URL with optional password
        password = cache_password()
        user = cache_user() or ''

        if password:
            redis_url = f'redis://{user}:{password}@{cache_host()}:{cache_port()}/0'
        else:
            redis_url = f'redis://{cache_host()}:{cache_port()}/0'

        keepalive_options = {
            'TCP_KEEPCNT': cache_setting('keepalive_count', 5, typecast=int),
            'TCP_KEEPIDLE': cache_setting('keepalive_idle', 1, typecast=int),
            'TCP_KEEPINTVL': cache_setting('keepalive_interval', 1, typecast=int),
            'TCP_USER_TIMEOUT': cache_setting('user_timeout', 1000, typecast=int),
        }

        return {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': redis_url,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'SOCKET_CONNECT_TIMEOUT': cache_setting(
                    'connect_timeout', 5, typecast=int
                ),
                'SOCKET_TIMEOUT': cache_setting('timeout', 3, typecast=int),
                'CONNECTION_POOL_KWARGS': {
                    'socket_keepalive': cache_setting(
                        'tcp_keepalive', True, typecast=bool
                    ),
                    'socket_keepalive_options': {
                        # Only include options which are available on this platform
                        # e.g. MacOS does not have TCP_KEEPIDLE and TCP_USER_TIMEOUT
                        getattr(socket, key): value
                        for key, value in keepalive_options.items()
                        if hasattr(socket, key)
                    },
                },
            },
        }

    # Default: Use django local memory cache
    return {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}


def create_session_cache(request) -> None:
    """Create an empty session cache."""
    thread_data.request = request
    thread_data.request_cache = {}


def delete_session_cache() -> None:
    """Remove the session cache once the request is complete."""
    if hasattr(thread_data, 'request'):
        del thread_data.request

    if hasattr(thread_data, 'request_cache'):
        del thread_data.request_cache


def get_session_cache(key: str) -> Any:
    """Return a cached value from the session cache."""
    # Only return a cached value if the request object is available too
    if not hasattr(thread_data, 'request'):
        return None

    request_cache = getattr(thread_data, 'request_cache', None)
    if request_cache is not None:
        val = request_cache.get(key, None)
        return val


def set_session_cache(key: str, value: Any) -> None:
    """Set a cached value in the session cache."""
    # Only set a cached value if the request object is available too
    if not hasattr(thread_data, 'request'):
        return

    request_cache = getattr(thread_data, 'request_cache', None)

    if request_cache is not None:
        request_cache[key] = value


def get_cached_content_types(cache_key: str = 'all_content_types') -> list:
    """Return a list of all ContentType objects, using session cache if possible."""
    from django.contrib.contenttypes.models import ContentType

    # Attempt to retrieve a list of ContentType objects from session cache
    if content_types := get_session_cache(cache_key):
        return content_types

    try:
        content_types = list(ContentType.objects.all())
        if len(content_types) > 0:
            set_session_cache(cache_key, content_types)
    except (OperationalError, ProgrammingError):
        # Database is likely not yet ready
        content_types = []

    return content_types
