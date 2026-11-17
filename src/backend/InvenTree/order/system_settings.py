"""System settings for order app."""

from django.utils.translation import gettext_lazy as _

import order.validators
from common.setting.type import InvenTreeSettingsKeyType, SettingFlag

SYSTEM_SETTINGS: dict[str, InvenTreeSettingsKeyType] = {
    # RO
    'RETURNORDER_ENABLED': {
        'name': _('Enable Return Orders'),
        'description': _('Enable return order functionality in the user interface'),
        'validator': bool,
        'default': False,
        'flags': [SettingFlag.TOGGLE],
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
    # SO
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
    'SALESORDER_BLOCK_INCOMPLETE_ITEM_TESTS': {
        'name': _('Block Incomplete Item Tests'),
        'description': _(
            'Prevent allocation of stock items to sales orders if required item tests are incomplete'
        ),
        'default': False,
        'validator': bool,
    },
    'SALESORDER_ENABLED': {
        'name': _('Enable Sales Orders'),
        'description': _('Enable sales order functionality in the user interface'),
        'validator': bool,
        'default': True,
        'flags': [SettingFlag.TOGGLE],
    },
    # TO
    'TRANSFERORDER_ENABLED': {
        'name': _('Enable Transfer Orders'),
        'description': _('Enable transfer order functionality in the user interface'),
        'validator': bool,
        'default': False,
        'flags': [SettingFlag.TOGGLE],
    },
    'TRANSFERORDER_REFERENCE_PATTERN': {
        'name': _('Transfer Order Reference Pattern'),
        'description': _(
            'Required pattern for generating Transfer Order reference field'
        ),
        'default': 'TO-{ref:04d}',
        'validator': order.validators.validate_transfer_order_reference_pattern,
    },
    'TRANSFERORDER_REQUIRE_RESPONSIBLE': {
        'name': _('Require Responsible Owner'),
        'description': _('A responsible owner must be assigned to each order'),
        'default': False,
        'validator': bool,
    },
    'TRANSFERORDER_EDIT_COMPLETED_ORDERS': {
        'name': _('Edit Completed Transfer Orders'),
        'description': _(
            'Allow editing of transfer orders after they have been completed'
        ),
        'default': False,
        'validator': bool,
    },
    # PO
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
    'PURCHASEORDER_MERGE_LINE_ITEMS': {
        'name': _('Merge Purchase Order Line Items'),
        'description': _(
            'Merge new purchase order line items with existing lines that share the same part, destination, and target date'
        ),
        'default': True,
        'validator': bool,
    },
    'PURCHASEORDER_DEFAULT_RECEIVE_LOCATION': {
        'name': _('Default Receive Location'),
        'description': _(
            'Default destination location for received goods on new purchase orders'
        ),
        'default': '',
        'model': 'stock.stocklocation',
        'model_filters': {'structural': False},
    },
    'PURCHASEORDER_ENABLED': {
        'name': _('Enable Purchase Orders'),
        'description': _('Enable purchase order functionality in the user interface'),
        'validator': bool,
        'default': True,
        'flags': [SettingFlag.TOGGLE],
    },
}
