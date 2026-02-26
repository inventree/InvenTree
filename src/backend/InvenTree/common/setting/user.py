"""User settings definition."""

from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from common.setting.type import InvenTreeSettingsKeyType
from plugin import PluginMixinEnum, registry


def label_printer_options():
    """Build a list of available label printer options."""
    printers = []
    label_printer_plugins = registry.with_mixin(PluginMixinEnum.LABELS)
    if label_printer_plugins:
        printers.extend([
            (p.slug, p.name + ' - ' + p.human_name) for p in label_printer_plugins
        ])
    return printers


USER_SETTINGS: dict[str, InvenTreeSettingsKeyType] = {
    'LABEL_INLINE': {
        'name': _('Inline label display'),
        'description': _(
            'Display PDF labels in the browser, instead of downloading as a file'
        ),
        'default': True,
        'validator': bool,
    },
    'LABEL_DEFAULT_PRINTER': {
        'name': _('Default label printer'),
        'description': _('Configure which label printer should be selected by default'),
        'default': '',
        'choices': label_printer_options,
    },
    'REPORT_INLINE': {
        'name': _('Inline report display'),
        'description': _(
            'Display PDF reports in the browser, instead of downloading as a file'
        ),
        'default': False,
        'validator': bool,
    },
    'BARCODE_IN_FORM_FIELDS': {
        'name': _('Barcode Scanner in Form Fields'),
        'description': _('Allow barcode scanner input in form fields'),
        'default': False,
        'validator': bool,
    },
    'SEARCH_PREVIEW_SHOW_PARTS': {
        'name': _('Search Parts'),
        'description': _('Display parts in search preview window'),
        'default': True,
        'validator': bool,
    },
    'SEARCH_PREVIEW_SHOW_SUPPLIER_PARTS': {
        'name': _('Search Supplier Parts'),
        'description': _('Display supplier parts in search preview window'),
        'default': True,
        'validator': bool,
    },
    'SEARCH_PREVIEW_SHOW_MANUFACTURER_PARTS': {
        'name': _('Search Manufacturer Parts'),
        'description': _('Display manufacturer parts in search preview window'),
        'default': True,
        'validator': bool,
    },
    'SEARCH_HIDE_INACTIVE_PARTS': {
        'name': _('Hide Inactive Parts'),
        'description': _('Excluded inactive parts from search preview window'),
        'default': False,
        'validator': bool,
    },
    'SEARCH_PREVIEW_SHOW_CATEGORIES': {
        'name': _('Search Categories'),
        'description': _('Display part categories in search preview window'),
        'default': False,
        'validator': bool,
    },
    'SEARCH_PREVIEW_SHOW_STOCK': {
        'name': _('Search Stock'),
        'description': _('Display stock items in search preview window'),
        'default': True,
        'validator': bool,
    },
    'SEARCH_PREVIEW_HIDE_UNAVAILABLE_STOCK': {
        'name': _('Hide Unavailable Stock Items'),
        'description': _(
            'Exclude stock items which are not available from the search preview window'
        ),
        'validator': bool,
        'default': False,
    },
    'SEARCH_PREVIEW_SHOW_LOCATIONS': {
        'name': _('Search Locations'),
        'description': _('Display stock locations in search preview window'),
        'default': False,
        'validator': bool,
    },
    'SEARCH_PREVIEW_SHOW_COMPANIES': {
        'name': _('Search Companies'),
        'description': _('Display companies in search preview window'),
        'default': True,
        'validator': bool,
    },
    'SEARCH_PREVIEW_SHOW_BUILD_ORDERS': {
        'name': _('Search Build Orders'),
        'description': _('Display build orders in search preview window'),
        'default': True,
        'validator': bool,
    },
    'SEARCH_PREVIEW_SHOW_PURCHASE_ORDERS': {
        'name': _('Search Purchase Orders'),
        'description': _('Display purchase orders in search preview window'),
        'default': True,
        'validator': bool,
    },
    'SEARCH_PREVIEW_EXCLUDE_INACTIVE_PURCHASE_ORDERS': {
        'name': _('Exclude Inactive Purchase Orders'),
        'description': _('Exclude inactive purchase orders from search preview window'),
        'default': True,
        'validator': bool,
    },
    'SEARCH_PREVIEW_SHOW_SALES_ORDERS': {
        'name': _('Search Sales Orders'),
        'description': _('Display sales orders in search preview window'),
        'default': True,
        'validator': bool,
    },
    'SEARCH_PREVIEW_EXCLUDE_INACTIVE_SALES_ORDERS': {
        'name': _('Exclude Inactive Sales Orders'),
        'description': _('Exclude inactive sales orders from search preview window'),
        'validator': bool,
        'default': True,
    },
    'SEARCH_PREVIEW_SHOW_SALES_ORDER_SHIPMENTS': {
        'name': _('Search Sales Order Shipments'),
        'description': _('Display sales order shipments in search preview window'),
        'default': True,
        'validator': bool,
    },
    'SEARCH_PREVIEW_SHOW_RETURN_ORDERS': {
        'name': _('Search Return Orders'),
        'description': _('Display return orders in search preview window'),
        'default': True,
        'validator': bool,
    },
    'SEARCH_PREVIEW_EXCLUDE_INACTIVE_RETURN_ORDERS': {
        'name': _('Exclude Inactive Return Orders'),
        'description': _('Exclude inactive return orders from search preview window'),
        'validator': bool,
        'default': True,
    },
    'SEARCH_PREVIEW_RESULTS': {
        'name': _('Search Preview Results'),
        'description': _(
            'Number of results to show in each section of the search preview window'
        ),
        'default': 10,
        'validator': [int, MinValueValidator(1)],
    },
    'SEARCH_REGEX': {
        'name': _('Regex Search'),
        'description': _('Enable regular expressions in search queries'),
        'default': False,
        'validator': bool,
    },
    'SEARCH_WHOLE': {
        'name': _('Whole Word Search'),
        'description': _('Search queries return results for whole word matches'),
        'default': False,
        'validator': bool,
    },
    'SEARCH_NOTES': {
        'name': _('Search Notes'),
        'description': _(
            "Search queries return results for matches from the item's notes"
        ),
        'default': False,
        'validator': bool,
    },
    'FORMS_CLOSE_USING_ESCAPE': {
        'name': _('Escape Key Closes Forms'),
        'description': _('Use the escape key to close modal forms'),
        'default': False,
        'validator': bool,
    },
    'STICKY_HEADER': {
        'name': _('Fixed Navbar'),
        'description': _('The navbar position is fixed to the top of the screen'),
        'default': False,
        'validator': bool,
    },
    'STICKY_TABLE_HEADER': {
        'name': _('Fixed Table Headers'),
        'description': _('Table headers are fixed to the top of the table'),
        'default': False,
        'validator': bool,
    },
    'SHOW_SPOTLIGHT': {
        'name': _('Show Spotlight'),
        'description': _('Enable spotlight navigation functionality'),
        'default': True,
        'validator': bool,
    },
    'ICONS_IN_NAVBAR': {
        'name': _('Navigation Icons'),
        'description': _('Display icons in the navigation bar'),
        'default': False,
        'validator': bool,
    },
    'DATE_DISPLAY_FORMAT': {
        'name': _('Date Format'),
        'description': _('Preferred format for displaying dates'),
        'default': 'YYYY-MM-DD',
        'choices': [
            ('YYYY-MM-DD', '2022-02-22'),
            ('YYYY/MM/DD', '2022/22/22'),
            ('DD-MM-YYYY', '22-02-2022'),
            ('DD/MM/YYYY', '22/02/2022'),
            ('MM-DD-YYYY', '02-22-2022'),
            ('MM/DD/YYYY', '02/22/2022'),
            ('MMM DD YYYY', 'Feb 22 2022'),
        ],
    },
    'DISPLAY_STOCKTAKE_TAB': {
        'name': _('Show Stock History'),
        'description': _('Display stock history information in the part detail page'),
        'default': True,
        'validator': bool,
    },
    'ENABLE_LAST_BREADCRUMB': {
        'name': _('Show Last Breadcrumb'),
        'description': _('Show the current page in breadcrumbs'),
        'default': False,
        'validator': bool,
    },
    'SHOW_FULL_LOCATION_IN_TABLES': {
        'name': _('Show full stock location in tables'),
        'description': _(
            'Disabled: The full location path is displayed as a hover tooltip. Enabled: The full location path is displayed as plain text.'
        ),
        'default': False,
        'validator': bool,
    },
    'SHOW_FULL_CATEGORY_IN_TABLES': {
        'name': _('Show full part categories in tables'),
        'description': _(
            'Disabled: The full category path is displayed as a hover tooltip. Enabled: The full category path is displayed as plain text.'
        ),
        'default': False,
        'validator': bool,
    },
    'NOTIFICATION_ERROR_REPORT': {
        'name': _('Receive error reports'),
        'description': _('Receive notifications for system errors'),
        'default': True,
        'validator': bool,
    },
    'LAST_USED_PRINTING_MACHINES': {
        'name': _('Last used printing machines'),
        'description': _('Save the last used printing machines for a user'),
        'default': '',
    },
}
