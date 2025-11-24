"""System settings definition."""

import json
import os
import re
import uuid

from django.conf import settings as django_settings
from django.contrib.auth.models import Group
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, URLValidator
from django.utils.translation import gettext_lazy as _

from jinja2 import Template

import build.validators
import common.currency
import common.validators
import order.validators
import report.helpers
from common.setting.type import InvenTreeSettingsKeyType


def validate_part_name_format(value):
    """Validate part name format.

    Make sure that each template container has a field of Part Model
    """
    # Make sure that the field_name exists in Part model
    from part.models import Part

    jinja_template_regex = re.compile(r'{{.*?}}')
    field_name_regex = re.compile(r'(?<=part\.)[A-z]+')

    for jinja_template in jinja_template_regex.findall(str(value)):
        # make sure at least one and only one field is present inside the parser
        field_names = field_name_regex.findall(jinja_template)
        if len(field_names) < 1:
            raise ValidationError({
                'value': 'At least one field must be present inside a jinja template container i.e {{}}'
            })

        for field_name in field_names:
            try:
                Part._meta.get_field(field_name)
            except FieldDoesNotExist:
                raise ValidationError({
                    'value': f'{field_name} does not exist in Part Model'
                })

    # Attempt to render the template with a dummy Part instance
    p = Part(name='test part', description='some test part')

    try:
        Template(value).render({'part': p})
    except Exception as exc:
        raise ValidationError({'value': str(exc)})

    return True


def update_instance_name(setting):
    """Update the first site objects name to instance name."""
    if not django_settings.SITE_MULTI:
        return

    try:
        from django.contrib.sites.models import Site
    except (ImportError, RuntimeError):
        # Multi-site support not enabled
        return

    site_obj = Site.objects.all().order_by('id').first()
    site_obj.name = setting.value
    site_obj.save()


def update_instance_url(setting):
    """Update the first site objects domain to url."""
    if not django_settings.SITE_MULTI:
        return

    try:
        from django.contrib.sites.models import Site
    except (ImportError, RuntimeError):
        # Multi-site support not enabled
        return

    site_obj = Site.objects.all().order_by('id').first()
    site_obj.domain = setting.value
    site_obj.save()


def settings_group_options():
    """Build up group tuple for settings based on your choices."""
    return [('', _('No group')), *[(str(a.id), str(a)) for a in Group.objects.all()]]


def reload_plugin_registry(setting):
    """When a core plugin setting is changed, reload the plugin registry."""
    from common.models import logger
    from plugin import registry

    logger.info("Reloading plugin registry due to change in setting '%s'", setting.key)

    registry.reload_plugins(full_reload=True, force_reload=True, collect=True)


def barcode_plugins() -> list:
    """Return a list of plugin choices which can be used for barcode generation."""
    try:
        from plugin import PluginMixinEnum, registry

        plugins = registry.with_mixin(PluginMixinEnum.BARCODE, active=True)
    except Exception:  # pragma: no cover
        plugins = []

    return [
        (plug.slug, plug.human_name) for plug in plugins if plug.has_barcode_generation
    ]


def default_uuid4() -> str:
    """Return a default UUID4 value."""
    return str(uuid.uuid4())


class BaseURLValidator(URLValidator):
    """Validator for the InvenTree base URL.

    Rules:
    - Allow empty value
    - Allow value without specified TLD (top level domain)
    """

    def __init__(self, schemes=None, **kwargs):
        """Custom init routine."""
        super().__init__(schemes, **kwargs)

        # Override default host_re value - allow optional tld regex
        self.host_re = (
            '('
            + self.hostname_re
            + self.domain_re
            + f'({self.tld_re})?'
            + '|localhost)'
        )

    def __call__(self, value):
        """Make sure empty values pass."""
        value = str(value).strip()

        # If a configuration level value has been specified, prevent change
        if django_settings.SITE_URL and value != django_settings.SITE_URL:
            raise ValidationError(_('Site URL is locked by configuration'))

        if len(value) == 0:
            pass

        else:
            super().__call__(value)


class SystemSetId:
    """Shared system settings identifiers."""

    GLOBAL_WARNING = '_GLOBAL_WARNING'


SYSTEM_SETTINGS: dict[str, InvenTreeSettingsKeyType] = {
    'SERVER_RESTART_REQUIRED': {
        'name': _('Restart required'),
        'description': _('A setting has been changed which requires a server restart'),
        'default': False,
        'validator': bool,
        'hidden': True,
    },
    '_PENDING_MIGRATIONS': {
        'name': _('Pending migrations'),
        'description': _('Number of pending database migrations'),
        'default': 0,
        'validator': int,
    },
    SystemSetId.GLOBAL_WARNING: {
        'name': _('Active warning codes'),
        'description': _('A dict of active warning codes'),
        'validator': json.loads,
        'default': '{}',
        'hidden': True,
    },
    'INVENTREE_INSTANCE_ID': {
        'name': _('Instance ID'),
        'description': _('Unique identifier for this InvenTree instance'),
        'default': default_uuid4,
        'hidden': True,
    },
    'INVENTREE_ANNOUNCE_ID': {
        'name': _('Announce ID'),
        'description': _(
            'Announce the instance ID of the server in the server status info (unauthenticated)'
        ),
        'default': False,
        'validator': bool,
    },
    'INVENTREE_INSTANCE': {
        'name': _('Server Instance Name'),
        'default': 'InvenTree',
        'description': _('String descriptor for the server instance'),
        'after_save': update_instance_name,
    },
    'INVENTREE_INSTANCE_TITLE': {
        'name': _('Use instance name'),
        'description': _('Use the instance name in the title-bar'),
        'validator': bool,
        'default': False,
    },
    'INVENTREE_RESTRICT_ABOUT': {
        'name': _('Restrict showing `about`'),
        'description': _('Show the `about` modal only to superusers'),
        'validator': bool,
        'default': False,
    },
    'INVENTREE_COMPANY_NAME': {
        'name': _('Company name'),
        'description': _('Internal company name'),
        'default': 'My company name',
    },
    'INVENTREE_BASE_URL': {
        'name': _('Base URL'),
        'description': _('Base URL for server instance'),
        'validator': BaseURLValidator(),
        'default': '',
        'after_save': update_instance_url,
    },
    'INVENTREE_DEFAULT_CURRENCY': {
        'name': _('Default Currency'),
        'description': _('Select base currency for pricing calculations'),
        'default': 'USD',
        'choices': common.currency.currency_code_mappings,
        'after_save': common.currency.after_change_currency,
    },
    'CURRENCY_CODES': {
        'name': _('Supported Currencies'),
        'description': _('List of supported currency codes'),
        'default': common.currency.currency_codes_default_list(),
        'validator': common.currency.validate_currency_codes,
        'after_save': common.currency.after_change_currency,
    },
    'CURRENCY_UPDATE_INTERVAL': {
        'name': _('Currency Update Interval'),
        'description': _('How often to update exchange rates (set to zero to disable)'),
        'default': 1,
        'units': _('days'),
        'validator': [int, MinValueValidator(0)],
    },
    'CURRENCY_UPDATE_PLUGIN': {
        'name': _('Currency Update Plugin'),
        'description': _('Currency update plugin to use'),
        'choices': common.currency.currency_exchange_plugins,
        'default': 'inventreecurrencyexchange',
    },
    'INVENTREE_DOWNLOAD_FROM_URL': {
        'name': _('Download from URL'),
        'description': _('Allow download of remote images and files from external URL'),
        'validator': bool,
        'default': False,
    },
    'INVENTREE_DOWNLOAD_IMAGE_MAX_SIZE': {
        'name': _('Download Size Limit'),
        'description': _('Maximum allowable download size for remote image'),
        'units': 'MB',
        'default': 1,
        'validator': [int, MinValueValidator(1), MaxValueValidator(25)],
    },
    'INVENTREE_DOWNLOAD_FROM_URL_USER_AGENT': {
        'name': _('User-agent used to download from URL'),
        'description': _(
            'Allow to override the user-agent used to download images and files from external URL (leave blank for the default)'
        ),
        'default': '',
    },
    'INVENTREE_STRICT_URLS': {
        'name': _('Strict URL Validation'),
        'description': _('Require schema specification when validating URLs'),
        'validator': bool,
        'default': True,
    },
    'INVENTREE_UPDATE_CHECK_INTERVAL': {
        'name': _('Update Check Interval'),
        'description': _('How often to check for updates (set to zero to disable)'),
        'validator': [int, MinValueValidator(0)],
        'default': 7,
        'units': _('days'),
    },
    'INVENTREE_BACKUP_ENABLE': {
        'name': _('Automatic Backup'),
        'description': _('Enable automatic backup of database and media files'),
        'validator': bool,
        'default': False,
    },
    'INVENTREE_BACKUP_DAYS': {
        'name': _('Auto Backup Interval'),
        'description': _('Specify number of days between automated backup events'),
        'validator': [int, MinValueValidator(1)],
        'default': 1,
        'units': _('days'),
    },
    'INVENTREE_DELETE_TASKS_DAYS': {
        'name': _('Task Deletion Interval'),
        'description': _(
            'Background task results will be deleted after specified number of days'
        ),
        'default': 30,
        'units': _('days'),
        'validator': [int, MinValueValidator(7)],
    },
    'INVENTREE_DELETE_ERRORS_DAYS': {
        'name': _('Error Log Deletion Interval'),
        'description': _('Error logs will be deleted after specified number of days'),
        'default': 30,
        'units': _('days'),
        'validator': [int, MinValueValidator(7)],
    },
    'INVENTREE_DELETE_NOTIFICATIONS_DAYS': {
        'name': _('Notification Deletion Interval'),
        'description': _(
            'User notifications will be deleted after specified number of days'
        ),
        'default': 30,
        'units': _('days'),
        'validator': [int, MinValueValidator(7)],
    },
    'INVENTREE_DELETE_EMAIL_DAYS': {
        'name': _('Email Deletion Interval'),
        'description': _(
            'Email messages will be deleted after specified number of days'
        ),
        'default': 30,
        'units': _('days'),
        'validator': [int, MinValueValidator(7)],
    },
    'INVENTREE_PROTECT_EMAIL_LOG': {
        'name': _('Protect Email Log'),
        'description': _('Prevent deletion of email log entries'),
        'default': False,
        'validator': bool,
    },
    'BARCODE_ENABLE': {
        'name': _('Barcode Support'),
        'description': _('Enable barcode scanner support in the web interface'),
        'default': True,
        'validator': bool,
    },
    'BARCODE_STORE_RESULTS': {
        'name': _('Store Barcode Results'),
        'description': _('Store barcode scan results in the database'),
        'default': False,
        'validator': bool,
    },
    'BARCODE_RESULTS_MAX_NUM': {
        'name': _('Barcode Scans Maximum Count'),
        'description': _('Maximum number of barcode scan results to store'),
        'default': 100,
        'validator': [int, MinValueValidator(1)],
    },
    'BARCODE_INPUT_DELAY': {
        'name': _('Barcode Input Delay'),
        'description': _('Barcode input processing delay time'),
        'default': 50,
        'validator': [int, MinValueValidator(1)],
        'units': 'ms',
    },
    'BARCODE_WEBCAM_SUPPORT': {
        'name': _('Barcode Webcam Support'),
        'description': _('Allow barcode scanning via webcam in browser'),
        'default': True,
        'validator': bool,
    },
    'BARCODE_SHOW_TEXT': {
        'name': _('Barcode Show Data'),
        'description': _('Display barcode data in browser as text'),
        'default': False,
        'validator': bool,
    },
    'BARCODE_GENERATION_PLUGIN': {
        'name': _('Barcode Generation Plugin'),
        'description': _('Plugin to use for internal barcode data generation'),
        'choices': barcode_plugins,
        'default': 'inventreebarcode',
    },
    'PART_ENABLE_REVISION': {
        'name': _('Part Revisions'),
        'description': _('Enable revision field for Part'),
        'validator': bool,
        'default': True,
    },
    'PART_REVISION_ASSEMBLY_ONLY': {
        'name': _('Assembly Revision Only'),
        'description': _('Only allow revisions for assembly parts'),
        'validator': bool,
        'default': False,
    },
    'PART_ALLOW_DELETE_FROM_ASSEMBLY': {
        'name': _('Allow Deletion from Assembly'),
        'description': _('Allow deletion of parts which are used in an assembly'),
        'validator': bool,
        'default': False,
    },
    'PART_IPN_REGEX': {
        'name': _('IPN Regex'),
        'description': _('Regular expression pattern for matching Part IPN'),
    },
    'PART_ALLOW_DUPLICATE_IPN': {
        'name': _('Allow Duplicate IPN'),
        'description': _('Allow multiple parts to share the same IPN'),
        'default': True,
        'validator': bool,
    },
    'PART_ALLOW_EDIT_IPN': {
        'name': _('Allow Editing IPN'),
        'description': _('Allow changing the IPN value while editing a part'),
        'default': True,
        'validator': bool,
    },
    'PART_COPY_BOM': {
        'name': _('Copy Part BOM Data'),
        'description': _('Copy BOM data by default when duplicating a part'),
        'default': True,
        'validator': bool,
    },
    'PART_COPY_PARAMETERS': {
        'name': _('Copy Part Parameter Data'),
        'description': _('Copy parameter data by default when duplicating a part'),
        'default': True,
        'validator': bool,
    },
    'PART_COPY_TESTS': {
        'name': _('Copy Part Test Data'),
        'description': _('Copy test data by default when duplicating a part'),
        'default': True,
        'validator': bool,
    },
    'PART_CATEGORY_PARAMETERS': {
        'name': _('Copy Category Parameter Templates'),
        'description': _('Copy category parameter templates when creating a part'),
        'default': True,
        'validator': bool,
    },
    'PART_TEMPLATE': {
        'name': _('Template'),
        'description': _('Parts are templates by default'),
        'default': False,
        'validator': bool,
    },
    'PART_ASSEMBLY': {
        'name': _('Assembly'),
        'description': _('Parts can be assembled from other components by default'),
        'default': False,
        'validator': bool,
    },
    'PART_COMPONENT': {
        'name': _('Component'),
        'description': _('Parts can be used as sub-components by default'),
        'default': True,
        'validator': bool,
    },
    'PART_PURCHASEABLE': {
        'name': _('Purchaseable'),
        'description': _('Parts are purchaseable by default'),
        'default': True,
        'validator': bool,
    },
    'PART_SALABLE': {
        'name': _('Salable'),
        'description': _('Parts are salable by default'),
        'default': False,
        'validator': bool,
    },
    'PART_TRACKABLE': {
        'name': _('Trackable'),
        'description': _('Parts are trackable by default'),
        'default': False,
        'validator': bool,
    },
    'PART_VIRTUAL': {
        'name': _('Virtual'),
        'description': _('Parts are virtual by default'),
        'default': False,
        'validator': bool,
    },
    'PART_SHOW_RELATED': {
        'name': _('Show related parts'),
        'description': _('Display related parts for a part'),
        'default': True,
        'validator': bool,
    },
    'PART_CREATE_INITIAL': {
        'name': _('Initial Stock Data'),
        'description': _('Allow creation of initial stock when adding a new part'),
        'default': False,
        'validator': bool,
    },
    'PART_CREATE_SUPPLIER': {
        'name': _('Initial Supplier Data'),
        'description': _(
            'Allow creation of initial supplier data when adding a new part'
        ),
        'default': True,
        'validator': bool,
    },
    'PART_NAME_FORMAT': {
        'name': _('Part Name Display Format'),
        'description': _('Format to display the part name'),
        'default': "{{ part.IPN if part.IPN }}{{ ' | ' if part.IPN }}{{ part.name }}{{ ' | ' if part.revision }}"
        '{{ part.revision if part.revision }}',
        'validator': validate_part_name_format,
    },
    'PART_CATEGORY_DEFAULT_ICON': {
        'name': _('Part Category Default Icon'),
        'description': _('Part category default icon (empty means no icon)'),
        'default': '',
        'validator': common.validators.validate_icon,
    },
    'PRICING_DECIMAL_PLACES_MIN': {
        'name': _('Minimum Pricing Decimal Places'),
        'description': _(
            'Minimum number of decimal places to display when rendering pricing data'
        ),
        'default': 0,
        'validator': [
            int,
            MinValueValidator(0),
            MaxValueValidator(4),
            common.validators.validate_decimal_places_min,
        ],
    },
    'PRICING_DECIMAL_PLACES': {
        'name': _('Maximum Pricing Decimal Places'),
        'description': _(
            'Maximum number of decimal places to display when rendering pricing data'
        ),
        'default': 6,
        'validator': [
            int,
            MinValueValidator(2),
            MaxValueValidator(6),
            common.validators.validate_decimal_places_max,
        ],
    },
    'PRICING_USE_SUPPLIER_PRICING': {
        'name': _('Use Supplier Pricing'),
        'description': _(
            'Include supplier price breaks in overall pricing calculations'
        ),
        'default': True,
        'validator': bool,
    },
    'PRICING_PURCHASE_HISTORY_OVERRIDES_SUPPLIER': {
        'name': _('Purchase History Override'),
        'description': _(
            'Historical purchase order pricing overrides supplier price breaks'
        ),
        'default': False,
        'validator': bool,
    },
    'PRICING_USE_STOCK_PRICING': {
        'name': _('Use Stock Item Pricing'),
        'description': _(
            'Use pricing from manually entered stock data for pricing calculations'
        ),
        'default': True,
        'validator': bool,
    },
    'PRICING_STOCK_ITEM_AGE_DAYS': {
        'name': _('Stock Item Pricing Age'),
        'description': _(
            'Exclude stock items older than this number of days from pricing calculations'
        ),
        'default': 0,
        'units': _('days'),
        'validator': [int, MinValueValidator(0)],
    },
    'PRICING_USE_VARIANT_PRICING': {
        'name': _('Use Variant Pricing'),
        'description': _('Include variant pricing in overall pricing calculations'),
        'default': True,
        'validator': bool,
    },
    'PRICING_ACTIVE_VARIANTS': {
        'name': _('Active Variants Only'),
        'description': _(
            'Only use active variant parts for calculating variant pricing'
        ),
        'default': False,
        'validator': bool,
    },
    'PRICING_AUTO_UPDATE': {
        'name': _('Auto Update Pricing'),
        'description': _(
            'Automatically update part pricing when internal data changes'
        ),
        'default': True,
        'validator': bool,
    },
    'PRICING_UPDATE_DAYS': {
        'name': _('Pricing Rebuild Interval'),
        'description': _('Number of days before part pricing is automatically updated'),
        'units': _('days'),
        'default': 30,
        'validator': [int, MinValueValidator(0)],
    },
    'PART_INTERNAL_PRICE': {
        'name': _('Internal Prices'),
        'description': _('Enable internal prices for parts'),
        'default': False,
        'validator': bool,
    },
    'PART_BOM_USE_INTERNAL_PRICE': {
        'name': _('Internal Price Override'),
        'description': _(
            'If available, internal prices override price range calculations'
        ),
        'default': False,
        'validator': bool,
    },
    'LABEL_ENABLE': {
        'name': _('Enable label printing'),
        'description': _('Enable label printing from the web interface'),
        'default': True,
        'validator': bool,
    },
    'LABEL_DPI': {
        'name': _('Label Image DPI'),
        'description': _(
            'DPI resolution when generating image files to supply to label printing plugins'
        ),
        'default': 300,
        'validator': [int, MinValueValidator(100)],
    },
    'REPORT_ENABLE': {
        'name': _('Enable Reports'),
        'description': _('Enable generation of reports'),
        'default': False,
        'validator': bool,
    },
    'REPORT_DEBUG_MODE': {
        'name': _('Debug Mode'),
        'description': _('Generate reports in debug mode (HTML output)'),
        'default': False,
        'validator': bool,
    },
    'REPORT_LOG_ERRORS': {
        'name': _('Log Report Errors'),
        'description': _('Log errors which occur when generating reports'),
        'default': False,
        'validator': bool,
    },
    'REPORT_DEFAULT_PAGE_SIZE': {
        'name': _('Page Size'),
        'description': _('Default page size for PDF reports'),
        'default': 'A4',
        'choices': report.helpers.report_page_size_options,
    },
    'PARAMETER_ENFORCE_UNITS': {
        'name': _('Enforce Parameter Units'),
        'description': _(
            'If units are provided, parameter values must match the specified units'
        ),
        'default': True,
        'validator': bool,
    },
    'SERIAL_NUMBER_GLOBALLY_UNIQUE': {
        'name': _('Globally Unique Serials'),
        'description': _('Serial numbers for stock items must be globally unique'),
        'default': False,
        'validator': bool,
    },
    'STOCK_DELETE_DEPLETED_DEFAULT': {
        'name': _('Delete Depleted Stock'),
        'description': _('Determines default behavior when a stock item is depleted'),
        'default': True,
        'validator': bool,
    },
    'STOCK_BATCH_CODE_TEMPLATE': {
        'name': _('Batch Code Template'),
        'description': _('Template for generating default batch codes for stock items'),
        'default': '',
    },
    'STOCK_ENABLE_EXPIRY': {
        'name': _('Stock Expiry'),
        'description': _('Enable stock expiry functionality'),
        'default': False,
        'validator': bool,
    },
    'STOCK_ALLOW_EXPIRED_SALE': {
        'name': _('Sell Expired Stock'),
        'description': _('Allow sale of expired stock'),
        'default': False,
        'validator': bool,
    },
    'STOCK_STALE_DAYS': {
        'name': _('Stock Stale Time'),
        'description': _(
            'Number of days stock items are considered stale before expiring'
        ),
        'default': 0,
        'units': _('days'),
        'validator': [int],
    },
    'STOCK_ALLOW_EXPIRED_BUILD': {
        'name': _('Build Expired Stock'),
        'description': _('Allow building with expired stock'),
        'default': False,
        'validator': bool,
    },
    'STOCK_OWNERSHIP_CONTROL': {
        'name': _('Stock Ownership Control'),
        'description': _('Enable ownership control over stock locations and items'),
        'default': False,
        'validator': bool,
    },
    'STOCK_LOCATION_DEFAULT_ICON': {
        'name': _('Stock Location Default Icon'),
        'description': _('Stock location default icon (empty means no icon)'),
        'default': '',
        'validator': common.validators.validate_icon,
    },
    'STOCK_SHOW_INSTALLED_ITEMS': {
        'name': _('Show Installed Stock Items'),
        'description': _('Display installed stock items in stock tables'),
        'default': False,
        'validator': bool,
    },
    'STOCK_ENFORCE_BOM_INSTALLATION': {
        'name': _('Check BOM when installing items'),
        'description': _(
            'Installed stock items must exist in the BOM for the parent part'
        ),
        'default': True,
        'validator': bool,
    },
    'STOCK_ALLOW_OUT_OF_STOCK_TRANSFER': {
        'name': _('Allow Out of Stock Transfer'),
        'description': _(
            'Allow stock items which are not in stock to be transferred between stock locations'
        ),
        'default': False,
        'validator': bool,
    },
    'BUILDORDER_REFERENCE_PATTERN': {
        'name': _('Build Order Reference Pattern'),
        'description': _('Required pattern for generating Build Order reference field'),
        'default': 'BO-{ref:04d}',
        'validator': build.validators.validate_build_order_reference_pattern,
    },
    'BUILDORDER_REQUIRE_RESPONSIBLE': {
        'name': _('Require Responsible Owner'),
        'description': _('A responsible owner must be assigned to each order'),
        'default': False,
        'validator': bool,
    },
    'BUILDORDER_REQUIRE_ACTIVE_PART': {
        'name': _('Require Active Part'),
        'description': _('Prevent build order creation for inactive parts'),
        'default': False,
        'validator': bool,
    },
    'BUILDORDER_REQUIRE_LOCKED_PART': {
        'name': _('Require Locked Part'),
        'description': _('Prevent build order creation for unlocked parts'),
        'default': False,
        'validator': bool,
    },
    'BUILDORDER_REQUIRE_VALID_BOM': {
        'name': _('Require Valid BOM'),
        'description': _('Prevent build order creation unless BOM has been validated'),
        'default': False,
        'validator': bool,
    },
    'BUILDORDER_REQUIRE_CLOSED_CHILDS': {
        'name': _('Require Closed Child Orders'),
        'description': _(
            'Prevent build order completion until all child orders are closed'
        ),
        'default': False,
        'validator': bool,
    },
    'BUILDORDER_EXTERNAL_BUILDS': {
        'name': _('External Build Orders'),
        'description': _('Enable external build order functionality'),
        'default': False,
        'validator': bool,
    },
    'PREVENT_BUILD_COMPLETION_HAVING_INCOMPLETED_TESTS': {
        'name': _('Block Until Tests Pass'),
        'description': _(
            'Prevent build outputs from being completed until all required tests pass'
        ),
        'default': False,
        'validator': bool,
    },
    'RETURNORDER_ENABLED': {
        'name': _('Enable Return Orders'),
        'description': _('Enable return order functionality in the user interface'),
        'validator': bool,
        'default': False,
    },
    'RETURNORDER_REFERENCE_PATTERN': {
        'name': _('Return Order Reference Pattern'),
        'description': _(
            'Required pattern for generating Return Order reference field'
        ),
        'default': 'RMA-{ref:04d}',
        'validator': order.validators.validate_return_order_reference_pattern,
    },
    'RETURNORDER_REQUIRE_RESPONSIBLE': {
        'name': _('Require Responsible Owner'),
        'description': _('A responsible owner must be assigned to each order'),
        'default': False,
        'validator': bool,
    },
    'RETURNORDER_EDIT_COMPLETED_ORDERS': {
        'name': _('Edit Completed Return Orders'),
        'description': _(
            'Allow editing of return orders after they have been completed'
        ),
        'default': False,
        'validator': bool,
    },
    'SALESORDER_REFERENCE_PATTERN': {
        'name': _('Sales Order Reference Pattern'),
        'description': _('Required pattern for generating Sales Order reference field'),
        'default': 'SO-{ref:04d}',
        'validator': order.validators.validate_sales_order_reference_pattern,
    },
    'SALESORDER_REQUIRE_RESPONSIBLE': {
        'name': _('Require Responsible Owner'),
        'description': _('A responsible owner must be assigned to each order'),
        'default': False,
        'validator': bool,
    },
    'SALESORDER_DEFAULT_SHIPMENT': {
        'name': _('Sales Order Default Shipment'),
        'description': _('Enable creation of default shipment with sales orders'),
        'default': False,
        'validator': bool,
    },
    'SALESORDER_EDIT_COMPLETED_ORDERS': {
        'name': _('Edit Completed Sales Orders'),
        'description': _(
            'Allow editing of sales orders after they have been shipped or completed'
        ),
        'default': False,
        'validator': bool,
    },
    'SALESORDER_SHIPMENT_REQUIRES_CHECK': {
        'name': _('Shipment Requires Checking'),
        'description': _(
            'Prevent completion of shipments until items have been checked'
        ),
        'default': False,
        'validator': bool,
    },
    'SALESORDER_SHIP_COMPLETE': {
        'name': _('Mark Shipped Orders as Complete'),
        'description': _(
            'Sales orders marked as shipped will automatically be completed, bypassing the "shipped" status'
        ),
        'default': False,
        'validator': bool,
    },
    'PURCHASEORDER_REFERENCE_PATTERN': {
        'name': _('Purchase Order Reference Pattern'),
        'description': _(
            'Required pattern for generating Purchase Order reference field'
        ),
        'default': 'PO-{ref:04d}',
        'validator': order.validators.validate_purchase_order_reference_pattern,
    },
    'PURCHASEORDER_REQUIRE_RESPONSIBLE': {
        'name': _('Require Responsible Owner'),
        'description': _('A responsible owner must be assigned to each order'),
        'default': False,
        'validator': bool,
    },
    'PURCHASEORDER_EDIT_COMPLETED_ORDERS': {
        'name': _('Edit Completed Purchase Orders'),
        'description': _(
            'Allow editing of purchase orders after they have been shipped or completed'
        ),
        'default': False,
        'validator': bool,
    },
    'PURCHASEORDER_CONVERT_CURRENCY': {
        'name': _('Convert Currency'),
        'description': _('Convert item value to base currency when receiving stock'),
        'default': False,
        'validator': bool,
    },
    'PURCHASEORDER_AUTO_COMPLETE': {
        'name': _('Auto Complete Purchase Orders'),
        'description': _(
            'Automatically mark purchase orders as complete when all line items are received'
        ),
        'default': True,
        'validator': bool,
    },
    # login / SSO
    'LOGIN_ENABLE_PWD_FORGOT': {
        'name': _('Enable password forgot'),
        'description': _('Enable password forgot function on the login pages'),
        'default': True,
        'validator': bool,
    },
    'LOGIN_ENABLE_REG': {
        'name': _('Enable registration'),
        'description': _('Enable self-registration for users on the login pages'),
        'default': False,
        'validator': bool,
    },
    'LOGIN_ENABLE_SSO': {
        'name': _('Enable SSO'),
        'description': _('Enable SSO on the login pages'),
        'default': False,
        'validator': bool,
    },
    'LOGIN_ENABLE_SSO_REG': {
        'name': _('Enable SSO registration'),
        'description': _(
            'Enable self-registration via SSO for users on the login pages'
        ),
        'default': False,
        'validator': bool,
    },
    'LOGIN_ENABLE_SSO_GROUP_SYNC': {
        'name': _('Enable SSO group sync'),
        'description': _(
            'Enable synchronizing InvenTree groups with groups provided by the IdP'
        ),
        'default': False,
        'validator': bool,
    },
    'SSO_GROUP_KEY': {
        'name': _('SSO group key'),
        'description': _('The name of the groups claim attribute provided by the IdP'),
        'default': 'groups',
        'validator': str,
    },
    'SSO_GROUP_MAP': {
        'name': _('SSO group map'),
        'description': _(
            'A mapping from SSO groups to local InvenTree groups. If the local group does not exist, it will be created.'
        ),
        'validator': json.loads,
        'default': '{}',
    },
    'SSO_REMOVE_GROUPS': {
        'name': _('Remove groups outside of SSO'),
        'description': _(
            'Whether groups assigned to the user should be removed if they are not backend by the IdP. Disabling this setting might cause security issues'
        ),
        'default': True,
        'validator': bool,
    },
    'LOGIN_MAIL_REQUIRED': {
        'name': _('Email required'),
        'description': _('Require user to supply mail on signup'),
        'default': False,
        'validator': bool,
    },
    'LOGIN_SIGNUP_SSO_AUTO': {
        'name': _('Auto-fill SSO users'),
        'description': _('Automatically fill out user-details from SSO account-data'),
        'default': True,
        'validator': bool,
    },
    'LOGIN_SIGNUP_MAIL_TWICE': {
        'name': _('Mail twice'),
        'description': _('On signup ask users twice for their mail'),
        'default': False,
        'validator': bool,
    },
    'LOGIN_SIGNUP_PWD_TWICE': {
        'name': _('Password twice'),
        'description': _('On signup ask users twice for their password'),
        'default': True,
        'validator': bool,
    },
    'LOGIN_SIGNUP_MAIL_RESTRICTION': {
        'name': _('Allowed domains'),
        'description': _(
            'Restrict signup to certain domains (comma-separated, starting with @)'
        ),
        'default': '',
        'before_save': common.validators.validate_email_domains,
    },
    'SIGNUP_GROUP': {
        'name': _('Group on signup'),
        'description': _(
            'Group to which new users are assigned on registration. If SSO group sync is enabled, this group is only set if no group can be assigned from the IdP.'
        ),
        'default': '',
        'choices': settings_group_options,
    },
    'LOGIN_ENFORCE_MFA': {
        'name': _('Enforce MFA'),
        'description': _('Users must use multifactor security.'),
        'default': False,
        'validator': bool,
    },
    'PLUGIN_ON_STARTUP': {
        'name': _('Check plugins on startup'),
        'description': _(
            'Check that all plugins are installed on startup - enable in container environments'
        ),
        'default': str(os.getenv('INVENTREE_DOCKER', 'False')).lower() in ['1', 'true'],
        'validator': bool,
        'requires_restart': True,
    },
    'PLUGIN_UPDATE_CHECK': {
        'name': _('Check for plugin updates'),
        'description': _('Enable periodic checks for updates to installed plugins'),
        'default': True,
        'validator': bool,
    },
    # Settings for plugin mixin features
    'ENABLE_PLUGINS_URL': {
        'name': _('Enable URL integration'),
        'description': _('Enable plugins to add URL routes'),
        'default': False,
        'validator': bool,
        'after_save': reload_plugin_registry,
    },
    'ENABLE_PLUGINS_NAVIGATION': {
        'name': _('Enable navigation integration'),
        'description': _('Enable plugins to integrate into navigation'),
        'default': False,
        'validator': bool,
        'after_save': reload_plugin_registry,
    },
    'ENABLE_PLUGINS_APP': {
        'name': _('Enable app integration'),
        'description': _('Enable plugins to add apps'),
        'default': False,
        'validator': bool,
        'after_save': reload_plugin_registry,
    },
    'ENABLE_PLUGINS_SCHEDULE': {
        'name': _('Enable schedule integration'),
        'description': _('Enable plugins to run scheduled tasks'),
        'default': False,
        'validator': bool,
        'after_save': reload_plugin_registry,
    },
    'ENABLE_PLUGINS_EVENTS': {
        'name': _('Enable event integration'),
        'description': _('Enable plugins to respond to internal events'),
        'default': False,
        'validator': bool,
        'after_save': reload_plugin_registry,
    },
    'ENABLE_PLUGINS_INTERFACE': {
        'name': _('Enable interface integration'),
        'description': _('Enable plugins to integrate into the user interface'),
        'default': False,
        'validator': bool,
        'after_save': reload_plugin_registry,
    },
    'ENABLE_PLUGINS_MAILS': {
        'name': _('Enable mail integration'),
        'description': _('Enable plugins to process outgoing/incoming mails'),
        'default': False,
        'validator': bool,
        'after_save': reload_plugin_registry,
    },
    'PROJECT_CODES_ENABLED': {
        'name': _('Enable project codes'),
        'description': _('Enable project codes for tracking projects'),
        'default': False,
        'validator': bool,
    },
    'STOCKTAKE_ENABLE': {
        'name': _('Enable Stock History'),
        'description': _(
            'Enable functionality for recording historical stock levels and value'
        ),
        'validator': bool,
        'default': False,
    },
    'STOCKTAKE_EXCLUDE_EXTERNAL': {
        'name': _('Exclude External Locations'),
        'description': _(
            'Exclude stock items in external locations from stock history calculations'
        ),
        'validator': bool,
        'default': False,
    },
    'STOCKTAKE_AUTO_DAYS': {
        'name': _('Automatic Stocktake Period'),
        'description': _('Number of days between automatic stock history recording'),
        'validator': [int, MinValueValidator(1)],
        'default': 7,
        'units': _('days'),
    },
    'STOCKTAKE_DELETE_OLD_ENTRIES': {
        'name': _('Delete Old Stock History Entries'),
        'description': _(
            'Delete stock history entries older than the specified number of days'
        ),
        'default': False,
        'validator': bool,
    },
    'STOCKTAKE_DELETE_DAYS': {
        'name': _('Stock History Deletion Interval'),
        'description': _(
            'Stock history entries will be deleted after specified number of days'
        ),
        'default': 365,
        'units': _('days'),
        'validator': [int, MinValueValidator(30)],
    },
    'DISPLAY_FULL_NAMES': {
        'name': _('Display Users full names'),
        'description': _('Display Users full names instead of usernames'),
        'default': False,
        'validator': bool,
    },
    'DISPLAY_PROFILE_INFO': {
        'name': _('Display User Profiles'),
        'description': _('Display Users Profiles on their profile page'),
        'default': True,
        'validator': bool,
    },
    'TEST_STATION_DATA': {
        'name': _('Enable Test Station Data'),
        'description': _('Enable test station data collection for test results'),
        'default': False,
        'validator': bool,
    },
    'MACHINE_PING_ENABLED': {
        'name': _('Enable Machine Ping'),
        'description': _(
            'Enable periodic ping task of registered machines to check their status'
        ),
        'default': True,
        'validator': bool,
    },
}
