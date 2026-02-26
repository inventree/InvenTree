"""Plugin to automatically issue orders on the assigned target date."""

from django.utils.translation import gettext_lazy as _

import structlog

from InvenTree.helpers import current_date
from plugin import InvenTreePlugin
from plugin.mixins import ScheduleMixin, SettingsMixin

logger = structlog.get_logger('inventree')


class AutoIssueOrdersPlugin(ScheduleMixin, SettingsMixin, InvenTreePlugin):
    """Plugin to automatically issue orders on the assigned target date."""

    NAME = _('Auto Issue Orders')
    SLUG = 'autoiissueorders'
    AUTHOR = _('InvenTree contributors')
    DESCRIPTION = _('Automatically issue orders on the assigned target date')
    VERSION = '1.0.0'

    # Set the scheduled tasks for this plugin
    SCHEDULED_TASKS = {
        'auto_issue_orders': {'func': 'auto_issue_orders', 'schedule': 'D'}
    }

    SETTINGS = {
        'AUTO_ISSUE_BUILD_ORDERS': {
            'name': _('Auto Issue Build Orders'),
            'description': _(
                'Automatically issue build orders on the assigned target date'
            ),
            'validator': bool,
            'default': True,
        },
        'AUTO_ISSUE_PURCHASE_ORDERS': {
            'name': _('Auto Issue Purchase Orders'),
            'description': _(
                'Automatically issue purchase orders on the assigned target date'
            ),
            'validator': bool,
            'default': True,
        },
        'AUTO_ISSUE_SALES_ORDERS': {
            'name': _('Auto Issue Sales Orders'),
            'description': _(
                'Automatically issue sales orders on the assigned target date'
            ),
            'validator': bool,
            'default': True,
        },
        'AUTO_ISSUE_RETURN_ORDERS': {
            'name': _('Auto Issue Return Orders'),
            'description': _(
                'Automatically issue return orders on the assigned target date'
            ),
            'validator': bool,
            'default': True,
        },
        'ISSUE_BACKDATED_ORDERS': {
            'name': _('Issue Backdated Orders'),
            'description': _('Automatically issue orders that are backdated'),
            'validator': bool,
            'default': False,
        },
    }

    def auto_issue_orders(self):
        """Automatically issue orders on the assigned target date."""
        if self.get_setting('AUTO_ISSUE_BUILD_ORDERS', backup_value=True):
            self.auto_issue_build_orders()

        if self.get_setting('AUTO_ISSUE_PURCHASE_ORDERS', backup_value=True):
            self.auto_issue_purchase_orders()

        if self.get_setting('AUTO_ISSUE_SALES_ORDERS', backup_value=True):
            self.auto_issue_sales_orders()

        if self.get_setting('AUTO_ISSUE_RETURN_ORDERS', backup_value=True):
            self.auto_issue_return_orders()

    def issue_func(self, model, status: int, func_name: str = 'issue_order'):
        """Helper function to issue orders of a given model and status."""
        orders = model.objects.filter(status=status)
        orders = orders.filter(target_date__isnull=False)

        if self.get_setting('ISSUE_BACKDATED_ORDERS', backup_value=False):
            orders = orders.filter(target_date__lte=current_date())
        else:
            orders = orders.filter(target_date=current_date())

        if orders.count() == 0:
            return

        logger.info('Auto-issuing %d orders for %s', orders.count(), model.__name__)

        for order in orders:
            try:
                getattr(order, func_name)()
            except Exception as e:
                logger.error('Failed to issue order %s: %s', order.pk, e)

    def auto_issue_build_orders(self):
        """Automatically issue build orders on the assigned target date."""
        from build.models import Build
        from build.status_codes import BuildStatus

        self.issue_func(Build, BuildStatus.PENDING, func_name='issue_build')

    def auto_issue_purchase_orders(self):
        """Automatically issue purchase orders on the assigned target date."""
        from order.models import PurchaseOrder
        from order.status_codes import PurchaseOrderStatus

        self.issue_func(PurchaseOrder, PurchaseOrderStatus.PENDING)

    def auto_issue_sales_orders(self):
        """Automatically issue sales orders on the assigned target date."""
        from order.models import SalesOrder
        from order.status_codes import SalesOrderStatus

        self.issue_func(SalesOrder, SalesOrderStatus.PENDING)

    def auto_issue_return_orders(self):
        """Automatically issue return orders on the assigned target date."""
        from order.models import ReturnOrder
        from order.status_codes import ReturnOrderStatus

        self.issue_func(ReturnOrder, ReturnOrderStatus.PENDING)
