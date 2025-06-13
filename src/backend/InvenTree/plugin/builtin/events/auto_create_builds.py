"""Plugin to automatically create build orders for assemblies."""

from django.utils.translation import gettext_lazy as _

import structlog

from build.events import BuildEvents
from build.models import Build
from plugin import InvenTreePlugin
from plugin.mixins import EventMixin, SettingsMixin

logger = structlog.get_logger('inventree')


class AutoCreateBuildsPlugin(EventMixin, SettingsMixin, InvenTreePlugin):
    """Plugin which automatically creates build orders for assemblies.

    This plugin can be used to automatically create new build orders based on certain events:

    - When a build order is issued, automatically generate child build orders for sub-assemblies

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
        },
        'AUTO_CANCEL_CHILD_BUILDS': {
            'name': _('Cancel Child Builds'),
            'description': _(
                'Automatically cancel child builds when the parent build is cancelled'
            ),
            'validator': bool,
            'default': True,
        },
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
        return event in [BuildEvents.CANCELLED, BuildEvents.ISSUED]

    def process_event(self, event, *args, **kwargs):
        """Process the triggered event."""
        if event == BuildEvents.ISSUED:
            # Find the build order which was issued
            if build_id := kwargs.get('id'):
                self.process_build(build_id)

        elif event == BuildEvents.CANCELLED:
            if build_id := kwargs.get('id'):
                self.cancel_build(build_id)

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

    def cancel_build(self, build_id: int):
        """Cancel child builds when the parent build is cancelled."""
        if not self.get_setting('AUTO_CANCEL_CHILD_BUILDS', backup_value=False):
            return

        try:
            build = Build.objects.get(pk=build_id)
        except (ValueError, Build.DoesNotExist):
            logger.error('Invalid build ID provided', build_id=build_id)
            return

        print('Cancelling child builds for:', build)

        # Cancel all child builds associated with this build
