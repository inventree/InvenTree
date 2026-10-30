"""Plugin to automatically create build orders for assemblies."""

import functools
import math
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import transaction
from django.utils.translation import gettext_lazy as _

import structlog

import part.models
from build.events import BuildEvents
from build.models import Build
from build.status_codes import BuildStatus, BuildStatusGroups
from InvenTree.tasks import offload_task
from plugin import InvenTreePlugin
from plugin.mixins import EventMixin, SettingsMixin
from plugin.registry import call_plugin_function

logger = structlog.get_logger('inventree')


class AutoCreateBuildsPlugin(EventMixin, SettingsMixin, InvenTreePlugin):
    """Plugin which automatically creates build orders for assemblies.

    This plugin can be used to automatically create new build orders based on certain events:

    - When a build order is issued, automatically generate child build orders for sub-assemblies

    Build orders are only created for parts which are have insufficient stock to fulfill the order.

    Child build orders can be cascaded further down the BOM tree (see the CASCADE_DEPTH setting).
    Each additional level is processed as a separate background task.
    """

    NAME = _('Auto Create Builds')
    SLUG = 'autocreatebuilds'
    AUTHOR = _('InvenTree contributors')
    DESCRIPTION = _('Automatically create build orders for assemblies')
    VERSION = '1.2.0'

    SETTINGS = {
        'CASCADE_DEPTH': {
            'name': _('Cascade Depth'),
            'description': _(
                'How many levels of the sub-assembly tree to generate child build orders for'
            ),
            'validator': [int, MinValueValidator(1)],
            'default': 1,
        }
    }

    def get_cascade_depth(self) -> int:
        """Return the configured cascade depth (minimum 1)."""
        try:
            depth = int(self.get_setting('CASCADE_DEPTH', backup_value=1))
        except (TypeError, ValueError):
            depth = 1

        return max(depth, 1)

    def wants_process_event(self, event) -> bool:
        """Return whether given event should be processed or not."""
        return event in [BuildEvents.ISSUED]

    def process_event(self, event, *args, **kwargs):
        """Process the triggered event."""
        build_id = kwargs.get('id')

        if not build_id:
            logger.error('No build ID provided for event', event=event)
            return

        if event == BuildEvents.ISSUED:
            self.create_child_builds(build_id, self.get_cascade_depth())

    def create_child_builds(self, build_id: int, depth: int = 1):
        """Generate child build orders for the specified build order.

        This method is idempotent - it can safely be run multiple times
        (or concurrently by multiple workers) for the same build order.

        Arguments:
            build_id: Primary key of the parent build order
            depth: Number of levels of the sub-assembly tree (including this one) to process
        """
        if depth < 1:
            return

        with transaction.atomic():
            # Lock the parent build, so that concurrent workers processing
            # the same build order are serialized against each other
            try:
                build = Build.objects.select_for_update().get(pk=build_id)
            except (ValueError, Build.DoesNotExist):
                logger.error('Invalid build ID provided', build_id=build_id)
                return

            if build.status not in BuildStatusGroups.ACTIVE_CODES:
                # Do not generate child builds for a cancelled or completed build
                return

            self.process_build(build)

            if depth > 1:
                # Cascade down to the next level of the sub-assembly tree
                # The tasks are only registered once the new child builds are committed
                for child_id in build.children.filter(
                    status__in=BuildStatusGroups.ACTIVE_CODES
                ).values_list('pk', flat=True):
                    transaction.on_commit(
                        functools.partial(
                            offload_task,
                            call_plugin_function,
                            self.slug,
                            'create_child_builds',
                            child_id,
                            depth - 1,
                            group='plugin',
                            raise_error=False,
                        )
                    )

    def process_build(self, build: Build):
        """Create child build orders for any sub-assemblies which have insufficient stock.

        Note: The caller is expected to hold a lock on the provided build order.
        """
        # Iterate through all sub-assemblies for the build order
        for bom_item in build.part.get_bom_items().filter(
            part.models.BomItem.consumable_filter(consumable=False),
            sub_part__assembly=True,
        ):
            subassembly = bom_item.sub_part

            with_variants = bom_item.allow_variants

            # Skip if a child build already exists for this sub-assembly
            # (e.g. the build was previously issued, or this task is being re-run)
            if with_variants:
                children = build.children.filter(
                    part__in=subassembly.get_descendants(include_self=True)
                )
            else:
                children = build.children.filter(part=subassembly)

            if children.exists():
                continue

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
            # Build quantity is an integer field, so round up to avoid under-production
            try:
                with transaction.atomic():
                    Build.objects.create(
                        part=subassembly,
                        parent=build,
                        title=f'Generated child build for {build.reference}',
                        project_code=build.project_code,
                        quantity=math.ceil(required_quantity),
                        responsible=build.responsible,
                        sales_order=build.sales_order,
                        start_date=build.start_date,
                        status=BuildStatus.PENDING,
                        target_date=build.target_date,
                    )
            except ValidationError as e:
                # e.g. the sub-assembly is inactive, or has an unvalidated BOM
                logger.warning(
                    'Could not create child build order',
                    build=build.reference,
                    part=subassembly.pk,
                    error=str(e),
                )
