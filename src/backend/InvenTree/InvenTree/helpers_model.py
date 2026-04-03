"""Provides helper functions used throughout the InvenTree project that access the database."""

from decimal import Decimal
from typing import Optional, cast
from urllib.parse import urljoin

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.utils import OperationalError, ProgrammingError
from django.utils.translation import gettext_lazy as _

import structlog
from djmoney.contrib.exchange.models import convert_money
from djmoney.money import Money

from common.notifications import (
    InvenTreeNotificationBodies,
    NotificationBody,
    trigger_notification,
)
from common.settings import get_global_setting
from InvenTree.cache import (
    get_cached_content_types,
    get_session_cache,
    set_session_cache,
)
from InvenTree.format import format_money
from InvenTree.ready import ignore_ready_warning

logger = structlog.get_logger('inventree')


def get_base_url(request=None) -> str:
    """Return the base URL for the InvenTree server.

    The base URL is determined in the following order of decreasing priority:

    1. If a request object is provided, use the request URL
    2. Multi-site is enabled, and the current site has a valid URL
    3. If settings.SITE_URL is set (e.g. in the Django settings), use that
    4. If the InvenTree setting INVENTREE_BASE_URL is set, use that
    """
    # Check if a request is provided
    if request:
        return request.build_absolute_uri('/')

    # Check if multi-site is enabled
    try:
        from django.contrib.sites.models import Site

        return Site.objects.get_current().domain
    except (ImportError, RuntimeError):
        pass

    # Check if a global site URL is provided
    if site_url := getattr(settings, 'SITE_URL', None):
        return site_url

    # Check if a global InvenTree setting is provided
    try:
        if site_url := get_global_setting('INVENTREE_BASE_URL', create=False):
            return cast(str, site_url)
    except (ProgrammingError, OperationalError):
        pass

    # No base URL available
    return ''


def construct_absolute_url(*arg, base_url=None, request=None):
    """Construct (or attempt to construct) an absolute URL from a relative URL.

    Args:
        *arg: The relative URL to construct
        base_url: The base URL to use for the construction (if not provided, will attempt to determine from settings)
        request: The request object to use for the construction (optional)
    """
    relative_url = '/'.join(arg)

    if not base_url:
        base_url = get_base_url(request=request)

    return urljoin(base_url, relative_url)


def render_currency(
    money: Money,
    decimal_places: Optional[int] = None,
    currency: Optional[str] = None,
    multiplier: Optional[Decimal] = None,
    min_decimal_places: Optional[int] = None,
    max_decimal_places: Optional[int] = None,
    include_symbol: bool = True,
):
    """Render a currency / Money object to a formatted string (e.g. for reports).

    Arguments:
        money: The Money instance to be rendered
        decimal_places: The number of decimal places to render to. If unspecified, uses the PRICING_DECIMAL_PLACES setting.
        currency: Optionally convert to the specified currency
        multiplier: An optional multiplier to apply to the money amount before rendering
        min_decimal_places: The minimum number of decimal places to render to. If unspecified, uses the PRICING_DECIMAL_PLACES_MIN setting.
        max_decimal_places: The maximum number of decimal places to render to. If unspecified, uses the PRICING_DECIMAL_PLACES setting.
        include_symbol: If True, include the currency symbol in the output
    """
    if money in [None, '']:
        return '-'

    if type(money) is not Money:
        # Try to convert to a Money object
        try:
            money = Money(
                Decimal(str(money)),
                currency or get_global_setting('INVENTREE_DEFAULT_CURRENCY'),
            )
        except Exception:
            raise ValidationError(
                f"render_currency: {_('Invalid money value')}: '{money}' ({type(money).__name__})"
            )

    if currency is not None:
        # Attempt to convert to the provided currency
        # If cannot be done, leave the original
        try:
            money = convert_money(money, currency)
        except Exception:
            pass

    if multiplier is not None:
        try:
            money *= Decimal(str(multiplier).strip())
        except Exception:
            raise ValidationError(
                f"render_currency: {_('Invalid multiplier value')}: '{multiplier}' ({type(multiplier).__name__})"
            )

    if min_decimal_places is None or not isinstance(min_decimal_places, (int, float)):
        min_decimal_places = get_global_setting('PRICING_DECIMAL_PLACES_MIN', 0)

    if max_decimal_places is None or not isinstance(max_decimal_places, (int, float)):
        max_decimal_places = get_global_setting('PRICING_DECIMAL_PLACES', 6)

    value = Decimal(str(money.amount)).normalize()
    value = str(value)

    if decimal_places is not None and isinstance(decimal_places, (int, float)):
        # Decimal place count is provided, use it
        pass
    elif '.' in value:
        # If the value has a decimal point, use the number of decimal places in the value
        decimal_places = len(value.split('.')[-1])
    else:
        # No decimal point, use 2 as a default
        decimal_places = 2

    # Clip the decimal places to the specified range
    decimal_places = max(decimal_places, min_decimal_places)
    decimal_places = min(decimal_places, max_decimal_places)

    return format_money(
        money, decimal_places=decimal_places, include_symbol=include_symbol
    )


@ignore_ready_warning
def getModelsWithMixin(mixin_class) -> list:
    """Return a list of database models that inherit from the given mixin class.

    Args:
        mixin_class: The mixin class to search for
    Returns:
        List of models that inherit from the given mixin class
    """
    # First, look in the session cache - to prevent repeated expensive comparisons
    cache_key = f'models_with_mixin_{mixin_class.__name__}'

    if cached_models := get_session_cache(cache_key):
        return cached_models

    content_types = get_cached_content_types()

    db_models = [x.model_class() for x in content_types if x is not None]

    models_with_mixin = [
        x for x in db_models if x is not None and issubclass(x, mixin_class)
    ]
    # sort to make resulting list deterministic (and easier to test)
    models_with_mixin.sort(key=lambda x: x._meta.label_lower)

    # Store the result in the session cache
    set_session_cache(cache_key, models_with_mixin)
    return models_with_mixin


def notify_responsible(
    instance,
    sender,
    content: NotificationBody = InvenTreeNotificationBodies.NewOrder,
    exclude=None,
    extra_users: Optional[list] = None,
):
    """Notify all responsible parties of a change in an instance.

    Parses the supplied content with the provided instance and sender and sends a notification to all responsible users,
    excluding the optional excluded list.

    Args:
        instance: The newly created instance
        sender: Sender model reference
        content (NotificationBody, optional): _description_. Defaults to InvenTreeNotificationBodies.NewOrder.
        exclude (User, optional): User instance that should be excluded. Defaults to None.
        extra_users (list, optional): List of extra users to notify. Defaults to None.
    """
    import InvenTree.ready

    if InvenTree.ready.isImportingData() or InvenTree.ready.isRunningMigrations():
        return

    users = [instance.responsible]

    if extra_users:
        users.extend(extra_users)

    notify_users(users, instance, sender, content=content, exclude=exclude)


def notify_users(
    users,
    instance,
    sender,
    content: NotificationBody = InvenTreeNotificationBodies.NewOrder,
    exclude=None,
):
    """Notify all passed users or groups.

    Parses the supplied content with the provided instance and sender and sends a notification to all users,
    excluding the optional excluded list.

    Args:
        users: List of users or groups to notify
        instance: The newly created instance
        sender: Sender model reference
        content (NotificationBody, optional): _description_. Defaults to InvenTreeNotificationBodies.NewOrder.
        exclude (User, optional): User instance that should be excluded. Defaults to None.
    """
    # Setup context for notification parsing
    content_context = {
        'instance': str(instance),
        'verbose_name': sender._meta.verbose_name,
        'app_label': sender._meta.app_label,
        'model_name': sender._meta.model_name,
    }

    # Setup notification context
    context = {
        'instance': instance,
        'name': content.name.format(**content_context),
        'message': content.message.format(**content_context),
        'link': construct_absolute_url(instance.get_absolute_url()),
        'template': {'subject': content.name.format(**content_context)},
    }

    tmp = content.template
    if tmp:
        context['template']['html'] = tmp.format(**content_context)

    # Create notification
    trigger_notification(
        instance,
        content.slug.format(**content_context),
        targets=users,
        target_exclude=[exclude],
        context=context,
    )
