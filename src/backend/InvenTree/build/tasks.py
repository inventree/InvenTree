"""Background task definitions for the BuildOrder app."""

from datetime import timedelta
from decimal import Decimal
from typing import Optional

from django.contrib.auth.models import User
from django.db import transaction
from django.utils.translation import gettext_lazy as _

import structlog
from opentelemetry import trace

import common.notifications
import InvenTree.helpers
import InvenTree.helpers_model
import InvenTree.tasks
from build.events import BuildEvents
from build.status_codes import BuildStatusGroups
from InvenTree.ready import isImportingData
from plugin.events import trigger_event

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger('inventree')


@tracer.start_as_current_span('auto_allocate_build')
def auto_allocate_build(build_id: int, **kwargs):
    """Run auto-allocation for a specified BuildOrder."""
    from build.models import Build

    build_order = Build.objects.get(pk=build_id)
    build_order.auto_allocate_stock(**kwargs)


@tracer.start_as_current_span('consume_build_stock')
def consume_build_stock(
    build_id: int,
    lines: Optional[list[int]] = None,
    items: Optional[dict] = None,
    user_id: int | None = None,
    **kwargs,
):
    """Consume stock for the specified BuildOrder.

    Arguments:
        build_id: The ID of the BuildOrder to consume stock for
        lines: Optional list of BuildLine IDs to consume
        items: Optional dict of BuildItem IDs (and quantities)to consume
        user_id: The ID of the user who initiated the stock consumption
    """
    from build.models import Build, BuildItem, BuildLine

    build = Build.objects.get(pk=build_id)
    user = User.objects.filter(pk=user_id).first() if user_id else None

    lines = lines or []
    items = items or {}
    notes = kwargs.pop('notes', '')

    # Extract the relevant BuildLine and BuildItem objects
    with transaction.atomic():
        # Consume each of the specified BuildLine objects
        for line_id in lines:
            if build_line := BuildLine.objects.filter(pk=line_id, build=build).first():
                for item in build_line.allocations.all():
                    item.complete_allocation(
                        quantity=item.quantity, notes=notes, user=user
                    )

        # Consume each of the specified BuildItem objects
        for item_id, quantity in items.items():
            if build_item := BuildItem.objects.filter(
                pk=item_id, build_line__build=build
            ).first():
                build_item.complete_allocation(
                    quantity=quantity, notes=notes, user=user
                )


@tracer.start_as_current_span('complete_build_allocations')
def complete_build_allocations(build_id: int, user_id: int):
    """Complete build allocations for a specified BuildOrder."""
    from build.models import Build

    build_order = Build.objects.get(pk=build_id)

    if user_id:
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            user = None
            logger.warning(
                'Could not complete build allocations for BuildOrder <%s> - User does not exist',
                build_id,
            )
    else:
        user = None

    build_order.complete_allocations(user)


@tracer.start_as_current_span('delete_build_outputs')
def delete_build_outputs(build_id: int, output_ids: list, **kwargs):
    """Delete (cancel) specified build outputs for a BuildOrder.

    Arguments:
        build_id: The ID of the BuildOrder
        output_ids: List of StockItem PKs to delete
    """
    from build.models import Build
    from stock.models import StockItem

    build = Build.objects.get(pk=build_id)

    with transaction.atomic():
        for output_id in output_ids:
            output = StockItem.objects.filter(pk=output_id).first()
            if output:
                build.delete_output(output)


@tracer.start_as_current_span('scrap_build_outputs')
def scrap_build_outputs(
    build_id: int,
    outputs: list,
    location_id: int,
    notes: str = '',
    discard_allocations: bool = False,
    user_id: int | None = None,
    **kwargs,
):
    """Scrap specified build outputs for a BuildOrder.

    Arguments:
        build_id: The ID of the BuildOrder
        outputs: List of dicts with 'output_id' and 'quantity'
        location_id: PK of the destination StockLocation
        notes: Reason for scrapping
        discard_allocations: If True, discard (not consume) allocations
        user_id: PK of the user initiating the action
    """
    from build.models import Build
    from stock.models import StockItem, StockLocation

    build = Build.objects.get(pk=build_id)
    location = StockLocation.objects.get(pk=location_id)
    user = User.objects.filter(pk=user_id).first() if user_id else None

    with transaction.atomic():
        for item in outputs:
            output = StockItem.objects.filter(pk=item['output_id']).first()
            if output:
                build.scrap_build_output(
                    output,
                    item.get('quantity'),
                    location,
                    user=user,
                    notes=notes,
                    discard_allocations=discard_allocations,
                )


@tracer.start_as_current_span('complete_build_outputs')
def complete_build_outputs(
    build_id: int,
    outputs: list,
    location_id: int | None,
    status: int,
    notes: str = '',
    user_id: int | None = None,
    **kwargs,
):
    """Complete specified build outputs for a BuildOrder.

    Arguments:
        build_id: The ID of the BuildOrder
        outputs: List of dicts with 'output_id' and optional 'quantity'
        location_id: PK of the destination StockLocation (or None)
        status: Stock status code to assign to completed outputs
        notes: Completion notes
        user_id: PK of the user initiating the action
    """
    from build.models import Build
    from stock.models import StockItem, StockLocation

    build = Build.objects.get(pk=build_id)
    location = (
        StockLocation.objects.filter(pk=location_id).first() if location_id else None
    )
    user = User.objects.filter(pk=user_id).first() if user_id else None

    required_tests = build.part.getRequiredTests()

    with transaction.atomic():
        for item in outputs:
            output = StockItem.objects.filter(pk=item['output_id']).first()
            if output:
                build.complete_build_output(
                    output,
                    user,
                    quantity=item.get('quantity'),
                    location=location,
                    status=status,
                    notes=notes,
                    required_tests=required_tests,
                )


@tracer.start_as_current_span('cancel_build')
def cancel_build(
    build_id: int,
    user_id: int,
    remove_allocated_stock: bool = False,
    remove_incomplete_outputs: bool = False,
):
    """Tasks to run after a BuildOrder is cancelled.

    Arguments:
        build_id: The ID of the BuildOrder which has been cancelled
        user_id: The ID of the user who cancelled the BuildOrder
        remove_allocated_stock: If True, consume any allocated stock
        remove_incomplete_outputs: If True, delete any incomplete build outputs

    """
    from build.models import Build

    build = Build.objects.get(pk=build_id)

    if remove_allocated_stock:
        complete_build_allocations(build_id, user_id)
    else:
        build.allocated_stock.all().delete()

    if remove_incomplete_outputs:
        build.build_outputs.filter(is_building=True).delete()

    # Notify users that the order has been canceled
    InvenTree.helpers_model.notify_responsible(
        build,
        Build,
        exclude=build.issued_by,
        content=common.notifications.InvenTreeNotificationBodies.OrderCanceled,
        extra_users=build.part.get_subscribers(),
    )

    trigger_event(BuildEvents.CANCELLED, id=build.pk)


@tracer.start_as_current_span('complete_build')
def complete_build(build_id: int, user_id: int, trim_allocated_stock: bool = False):
    """Tasks to run after a BuildOrder is completed.

    Arguments:
        build_id: The ID of the BuildOrder which has been completed
        user_id: The ID of the user who completed the BuildOrder
        trim_allocated_stock: If True, trim any allocated stock which was not consumed
    """
    from build.models import Build

    build = Build.objects.get(pk=build_id)
    user = User.objects.filter(pk=user_id).first() if user_id else None

    if trim_allocated_stock:
        build.trim_allocated_stock()

    # Complete any remaining allocations for this build order
    complete_build_allocations(build_id, user_id)

    # Register an event
    trigger_event(BuildEvents.COMPLETED, id=build.pk)

    # Notify users that this build has been completed
    targets = [build.issued_by, build.responsible]

    # Also inform anyone subscribed to the assembly part
    targets.extend(build.part.get_subscribers())

    # Notify those users interested in the parent build
    if build.parent:
        targets.append(build.parent.issued_by)
        targets.append(build.parent.responsible)

    # Notify users if this build points to a sales order
    if build.sales_order:
        targets.append(build.sales_order.created_by)
        targets.append(build.sales_order.responsible)

    name = _(f'Build order {build} has been completed')

    context = {
        'build': build,
        'name': name,
        'slug': 'build.completed',
        'message': _('A build order has been completed'),
        'link': InvenTree.helpers_model.construct_absolute_url(
            build.get_absolute_url()
        ),
        'template': {'html': 'email/build_order_completed.html', 'subject': name},
    }

    common.notifications.trigger_notification(
        build,
        'build.completed',
        targets=targets,
        context=context,
        target_exclude=[user],
    )


@tracer.start_as_current_span('update_build_order_lines')
def update_build_order_lines(bom_item_pk: int):
    """Update all BuildOrderLineItem objects which reference a particular BomItem.

    This task is triggered when a BomItem is created or updated.
    """
    from build.models import Build, BuildLine
    from part.models import BomItem

    logger.info('Updating build order lines for BomItem %s', bom_item_pk)

    bom_item = BomItem.objects.filter(pk=bom_item_pk).first()

    # If the BomItem has been deleted, there is nothing to do
    if not bom_item:
        return

    assemblies = bom_item.get_assemblies()

    # Find all active builds which reference any of the parts
    builds = Build.objects.filter(
        part__in=list(assemblies), status__in=BuildStatusGroups.ACTIVE_CODES
    )

    # Iterate through each build, and update the relevant line items
    for bo in builds:
        # Try to find a matching build order line
        line = BuildLine.objects.filter(build=bo, bom_item=bom_item).first()

        q = bom_item.get_required_quantity(bo.quantity)

        if line:
            # If the BOM item points to a "virtual" part, delete the BuildLine instance
            if bom_item.sub_part.virtual:
                line.delete()
                continue

            # Ensure quantity is correct
            if line.quantity != q:
                line.quantity = q
                line.save()
        elif not bom_item.sub_part.virtual:
            # Create a new line item (for non-virtual parts)
            BuildLine.objects.create(build=bo, bom_item=bom_item, quantity=q)

    if builds.count() > 0:
        logger.info(
            'Updated %s build orders for part %s', builds.count(), bom_item.part
        )


@tracer.start_as_current_span('check_build_stock')
def check_build_stock(build):
    """Check the required stock for a newly created build order.

    Send an email out to any subscribed users if stock is low.
    """
    from part.models import Part

    # Do not notify if we are importing data
    if isImportingData():
        return

    # Iterate through each of the parts required for this build

    lines = []

    if not build:
        logger.error("Invalid build passed to 'build.tasks.check_build_stock'")
        return

    try:
        part = build.part
    except Part.DoesNotExist:
        # Note: This error may be thrown during unit testing...
        logger.exception("Invalid build.part passed to 'build.tasks.check_build_stock'")
        return

    # Iterate through each non-virtual BOM item for this part
    for bom_item in part.get_bom_items(include_virtual=False):
        sub_part = bom_item.sub_part

        # The 'in stock' quantity depends on whether the bom_item allows variants
        in_stock = sub_part.get_stock_count(include_variants=bom_item.allow_variants)

        allocated = sub_part.allocation_count()

        available = max(0, in_stock - allocated)

        required = Decimal(bom_item.quantity) * Decimal(build.quantity)

        if available < required:
            # There is not sufficient stock for this part

            lines.append({
                'link': InvenTree.helpers_model.construct_absolute_url(
                    sub_part.get_absolute_url()
                ),
                'part': sub_part,
                'in_stock': in_stock,
                'allocated': allocated,
                'available': available,
                'required': required,
            })

    if len(lines) == 0:
        # Nothing to do
        return

    # Are there any users subscribed to these parts?
    targets = build.part.get_subscribers()

    if build.responsible:
        targets.append(build.responsible)

    name = _('Stock required for build order')

    context = {
        'build': build,
        'name': name,
        'part': build.part,
        'lines': lines,
        'link': InvenTree.helpers_model.construct_absolute_url(
            build.get_absolute_url()
        ),
        'message': _('Build order {build} requires additional stock').format(
            build=build
        ),
        'template': {'html': 'email/build_order_required_stock.html', 'subject': name},
    }

    common.notifications.trigger_notification(
        build, BuildEvents.STOCK_REQUIRED, targets=targets, context=context
    )


@tracer.start_as_current_span('notify_overdue_build_order')
def notify_overdue_build_order(bo):
    """Notify appropriate users that a Build has just become 'overdue'."""
    targets = []

    if bo.issued_by:
        targets.append(bo.issued_by)

    if bo.responsible:
        targets.append(bo.responsible)

    targets.extend(bo.part.get_subscribers())

    name = _('Overdue Build Order')

    context = {
        'order': bo,
        'name': name,
        'message': _(f'Build order {bo} is now overdue'),
        'link': InvenTree.helpers_model.construct_absolute_url(bo.get_absolute_url()),
        'template': {'html': 'email/overdue_build_order.html', 'subject': name},
    }

    event_name = BuildEvents.OVERDUE

    # Send a notification to the appropriate users
    common.notifications.trigger_notification(
        bo, event_name, targets=targets, context=context
    )

    # Register a matching event to the plugin system
    trigger_event(event_name, build_order=bo.pk)


@tracer.start_as_current_span('check_overdue_build_orders')
@InvenTree.tasks.scheduled_task(InvenTree.tasks.ScheduledTask.DAILY)
def check_overdue_build_orders():
    """Check if any outstanding BuildOrders have just become overdue.

    - This check is performed daily
    - Look at the 'target_date' of any outstanding BuildOrder objects
    - If the 'target_date' expired *yesterday* then the order is just out of date
    """
    from build.models import Build

    yesterday = InvenTree.helpers.current_date() - timedelta(days=1)

    overdue_orders = Build.objects.filter(
        target_date=yesterday, status__in=BuildStatusGroups.ACTIVE_CODES
    )

    for bo in overdue_orders:
        notify_overdue_build_order(bo)
