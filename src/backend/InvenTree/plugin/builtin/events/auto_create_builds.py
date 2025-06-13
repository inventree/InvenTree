"""Plugin to automatically create build orders for assemblies."""

from decimal import Decimal

from django.utils.translation import gettext_lazy as _

import structlog

from build.events import BuildEvents
from build.models import Build
from build.status_codes import BuildStatus
from plugin import InvenTreePlugin
from plugin.mixins import EventMixin

logger = structlog.get_logger('inventree')


class AutoCreateBuildsPlugin(EventMixin, InvenTreePlugin):
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

    def wants_process_event(self, event) -> bool:
        """Return whether given event should be processed or not."""
        return event in [BuildEvents.CANCELLED]

    def process_event(self, event, *args, **kwargs):
        """Process the triggered event."""
        build_id = kwargs.get('id')

        if not build_id:
            logger.error('No build ID provided for event', event=event)
            return

        try:
            build = Build.objects.get(pk=build_id)
        except (ValueError, Build.DoesNotExist):
            logger.error('Invalid build ID provided', build_id=build_id)
            return

        if event == BuildEvents.ISSUED:
            self.process_build(build)

    def process_build(self, build: Build):
        """Process a build order when it is issued."""
        # Iterate through all sub-assemblies for the build order
        for bom_item in build.part.get_bom_items().filter(
            consumable=False, sub_part__assembly=True
        ):
            subassembly = bom_item.sub_part

            with_variants = bom_item.allow_variants

            # Quantity required for this particular build order
            build_quantity = bom_item.get_required_quantity(build.quantity)

            # Total existing stock for the sub-assembly
            stock_quantity = subassembly.get_stock_count(include_variants=with_variants)

            # How many of the sub-assembly are already allocated?
            allocated_quantity = subassembly.allocation_count(
                include_variants=with_variants
            )

            # Quantity of item already scheduled for production?
            in_production_quantity = subassembly.quantity_being_built

            # Determine if there is sufficient stock for the sub-assembly
            required_quantity = (
                Decimal(build_quantity)
                + Decimal(subassembly.minimum_stock)
                + Decimal(allocated_quantity)
                - Decimal(stock_quantity)
                - Decimal(in_production_quantity)
            )

            if required_quantity <= 0:
                # No need to build this sub-assembly
                continue

            # Generate a new build order for the sub-assembly
            Build.objects.create(
                part=subassembly,
                parent=build,
                project_code=build.project_code,
                quantity=required_quantity,
                responsible=build.responsible,
                sales_order=build.sales_order,
                start_date=build.start_date,
                status=BuildStatus.PENDING,
                target_date=build.target_date,
            )
