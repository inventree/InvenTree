"""Provides helper functions used throughout the InvenTree project that access the database."""

import io
import logging
from decimal import Decimal
from urllib.parse import urljoin

from django.conf import settings
from django.core.validators import URLValidator
from django.db.utils import OperationalError, ProgrammingError
from django.utils.translation import gettext_lazy as _

import requests
from djmoney.contrib.exchange.models import convert_money
from djmoney.money import Money
from PIL import Image

import common.models
import InvenTree
import InvenTree.helpers_model
import InvenTree.version
from common.notifications import (
    InvenTreeNotificationBodies,
    NotificationBody,
    trigger_notification,
)
from InvenTree.format import format_money

logger = logging.getLogger('inventree')


def getSetting(key, backup_value=None):
    """Shortcut for reading a setting value from the database."""
    return common.models.InvenTreeSetting.get_setting(key, backup_value=backup_value)


def get_base_url(request=None):
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
        if site_url := common.models.InvenTreeSetting.get_setting(
            'INVENTREE_BASE_URL', create=False, cache=False
        ):
            return site_url
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


def download_image_from_url(remote_url, timeout=2.5):
    """Download an image file from a remote URL.

    This is a potentially dangerous operation, so we must perform some checks:
    - The remote URL is available
    - The Content-Length is provided, and is not too large
    - The file is a valid image file

    Arguments:
        remote_url: The remote URL to retrieve image
        max_size: Maximum allowed image size (default = 1MB)
        timeout: Connection timeout in seconds (default = 5)

    Returns:
        An in-memory PIL image file, if the download was successful

    Raises:
        requests.exceptions.ConnectionError: Connection could not be established
        requests.exceptions.Timeout: Connection timed out
        requests.exceptions.HTTPError: Server responded with invalid response code
        ValueError: Server responded with invalid 'Content-Length' value
        TypeError: Response is not a valid image
    """
    # Check that the provided URL at least looks valid
    validator = URLValidator()
    validator(remote_url)

    # Calculate maximum allowable image size (in bytes)
    max_size = (
        int(
            common.models.InvenTreeSetting.get_setting(
                'INVENTREE_DOWNLOAD_IMAGE_MAX_SIZE'
            )
        )
        * 1024
        * 1024
    )

    # Add user specified user-agent to request (if specified)
    user_agent = common.models.InvenTreeSetting.get_setting(
        'INVENTREE_DOWNLOAD_FROM_URL_USER_AGENT'
    )
    if user_agent:
        headers = {'User-Agent': user_agent}
    else:
        headers = None

    try:
        response = requests.get(
            remote_url,
            timeout=timeout,
            allow_redirects=True,
            stream=True,
            headers=headers,
        )
        # Throw an error if anything goes wrong
        response.raise_for_status()
    except requests.exceptions.ConnectionError as exc:
        raise Exception(_('Connection error') + f': {str(exc)}')
    except requests.exceptions.Timeout as exc:
        raise exc
    except requests.exceptions.HTTPError:
        raise requests.exceptions.HTTPError(
            _('Server responded with invalid status code') + f': {response.status_code}'
        )
    except Exception as exc:
        raise Exception(_('Exception occurred') + f': {str(exc)}')

    if response.status_code != 200:
        raise Exception(
            _('Server responded with invalid status code') + f': {response.status_code}'
        )

    try:
        content_length = int(response.headers.get('Content-Length', 0))
    except ValueError:
        raise ValueError(_('Server responded with invalid Content-Length value'))

    if content_length > max_size:
        raise ValueError(_('Image size is too large'))

    # Download the file, ensuring we do not exceed the reported size
    file = io.BytesIO()

    dl_size = 0
    chunk_size = 64 * 1024

    for chunk in response.iter_content(chunk_size=chunk_size):
        dl_size += len(chunk)

        if dl_size > max_size:
            raise ValueError(_('Image download exceeded maximum size'))

        file.write(chunk)

    if dl_size == 0:
        raise ValueError(_('Remote server returned empty response'))

    # Now, attempt to convert the downloaded data to a valid image file
    # img.verify() will throw an exception if the image is not valid
    try:
        img = Image.open(file).convert()
        img.verify()
    except Exception:
        raise TypeError(_('Supplied URL is not a valid image file'))

    return img


def render_currency(
    money,
    decimal_places=None,
    currency=None,
    min_decimal_places=None,
    max_decimal_places=None,
    include_symbol=True,
):
    """Render a currency / Money object to a formatted string (e.g. for reports).

    Arguments:
        money: The Money instance to be rendered
        decimal_places: The number of decimal places to render to. If unspecified, uses the PRICING_DECIMAL_PLACES setting.
        currency: Optionally convert to the specified currency
        min_decimal_places: The minimum number of decimal places to render to. If unspecified, uses the PRICING_DECIMAL_PLACES_MIN setting.
        max_decimal_places: The maximum number of decimal places to render to. If unspecified, uses the PRICING_DECIMAL_PLACES setting.
        include_symbol: If True, include the currency symbol in the output
    """
    if money in [None, '']:
        return '-'

    if type(money) is not Money:
        return '-'

    if currency is not None:
        # Attempt to convert to the provided currency
        # If cannot be done, leave the original
        try:
            money = convert_money(money, currency)
        except Exception:
            pass

    if decimal_places is None:
        decimal_places = common.models.InvenTreeSetting.get_setting(
            'PRICING_DECIMAL_PLACES', 6
        )

    if min_decimal_places is None:
        min_decimal_places = common.models.InvenTreeSetting.get_setting(
            'PRICING_DECIMAL_PLACES_MIN', 0
        )

    if max_decimal_places is None:
        max_decimal_places = common.models.InvenTreeSetting.get_setting(
            'PRICING_DECIMAL_PLACES', 6
        )

    value = Decimal(str(money.amount)).normalize()
    value = str(value)

    if '.' in value:
        decimals = len(value.split('.')[-1])

        decimals = max(decimals, min_decimal_places)
        decimals = min(decimals, decimal_places)

        decimal_places = decimals
    else:
        decimal_places = max(decimal_places, 2)

    decimal_places = max(decimal_places, max_decimal_places)

    return format_money(
        money, decimal_places=decimal_places, include_symbol=include_symbol
    )


def getModelsWithMixin(mixin_class) -> list:
    """Return a list of models that inherit from the given mixin class.

    Args:
        mixin_class: The mixin class to search for
    Returns:
        List of models that inherit from the given mixin class
    """
    from django.contrib.contenttypes.models import ContentType

    try:
        db_models = [
            x.model_class() for x in ContentType.objects.all() if x is not None
        ]
    except (OperationalError, ProgrammingError):
        # Database is likely not yet ready
        db_models = []

    return [x for x in db_models if x is not None and issubclass(x, mixin_class)]


def notify_responsible(
    instance,
    sender,
    content: NotificationBody = InvenTreeNotificationBodies.NewOrder,
    exclude=None,
):
    """Notify all responsible parties of a change in an instance.

    Parses the supplied content with the provided instance and sender and sends a notification to all responsible users,
    excluding the optional excluded list.

    Args:
        instance: The newly created instance
        sender: Sender model reference
        content (NotificationBody, optional): _description_. Defaults to InvenTreeNotificationBodies.NewOrder.
        exclude (User, optional): User instance that should be excluded. Defaults to None.
    """
    import InvenTree.ready

    if InvenTree.ready.isImportingData() or InvenTree.ready.isRunningMigrations():
        return

    notify_users(
        [instance.responsible], instance, sender, content=content, exclude=exclude
    )


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
        'link': InvenTree.helpers_model.construct_absolute_url(
            instance.get_absolute_url()
        ),
        'template': {'subject': content.name.format(**content_context)},
    }

    if content.template:
        context['template']['html'] = content.template.format(**content_context)

    # Create notification
    trigger_notification(
        instance,
        content.slug.format(**content_context),
        targets=users,
        target_exclude=[exclude],
        context=context,
    )
