"""Plugin to automatically create build orders for assemblies."""

from django.utils.translation import gettext_lazy as _

import structlog

from build.events import BuildEvents
from build.models import Build
from order.events import SalesOrderEvents
from plugin import InvenTreePlugin
from plugin.mixins import EventMixin, SettingsMixin

logger = structlog.get_logger('inventree')


class AutoCreateBuildsPlugin(EventMixin, SettingsMixin, InvenTreePlugin):
    """Plugin which automatically creates build orders for assemblies.

    This plugin can be used to automatically create new build orders based on certain events:

    - When a build order is issued, automatically generate child build orders for sub-assemblies
    - When a sales order is issued, automatically generate build orders for assembled items

    Build orders are only created for parts which are have insufficient stock to fulfill the order.
    """

    NAME = _('Auto Create Builds')
    SLUG = 'autocreatebuilds'
    AUTHOR = _('InvenTree contributors')
    DESCRIPTION = _('Automatically create build orders for assemblies')
    VERSION = '1.0.0'

    SETTINGS = {
        'AUTO_CREATE_FOR_BUILD_ORDERS': {
            'name': _('Create Child Build Orders'),
            'description': _(
                'Automatically create build orders for subassemblies when a build order is issued'
            ),
            'validator': bool,
            'default': True,
        }
        # TODO: Future work - allow auto-creation of build orders for sales orders
        # 'AUTO_CREATE_FOR_SALES_ORDERS': {
        #     'name': _('Create Build Orders for Sales Orders'),
        #     'description': _(
        #         'Automatically create build orders for assembled items when a sales order is issued'
        #     ),
        #     'validator': bool,
        #     'default': True,
        # },
    }

    def wants_process_event(self, event) -> bool:
        """Return whether given event should be processed or not."""
        return event in [BuildEvents.ISSUED, SalesOrderEvents.ISSUED]

    def process_event(self, event, *args, **kwargs):
        """Process the triggered event."""
        print('process_event:', event)

        if event == BuildEvents.ISSUED:
            # Find the build order which was issued
            if build_id := kwargs.pop('build_id', None):
                self.process_build(build_id)

    def process_build(self, build_id: int):
        """Process a build order when it is issued."""
        if not self.get_setting('AUTO_CREATE_FOR_BUILD_ORDERS', backup_value=False):
            return

        try:
            build = Build.objects.get(pk=build_id)
        except (ValueError, Build.DoesNotExist):
            logger.error('Invalid build ID provided', build_id=build_id)
            return

        print('Processing build order:', build)

        # Iterate through all sub-assemblies for the build order
        for bom_item in build.part.get_bom_items().filter(
            consumable=False, sub_part__assembly=True
        ):
            subassembly = bom_item.sub_part

            print('- checking subassembly:', subassembly)

            # Determine if there is sufficient stock for the sub-assembly
