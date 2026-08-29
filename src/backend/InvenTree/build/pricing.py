"""Material cost calculation helpers for the 'build' app.

See dev/todo/pricing.md ("Manufacturing Costs") for the design this implements.

Note:
    This only accounts for the cost of BOM components consumed by a build
    (CostType.MATERIAL / MATERIAL_ESTIMATED) - manufacturing *process* cost
    (labor, overhead - CostType.MANUFACTURING) is not yet calculated anywhere.

Note:
    Consumable and virtual BOM lines are not yet accounted for here - see the
    "Manufacturing Costs" section of dev/todo/pricing.md for the follow-up plan.
"""

from django.core.exceptions import ObjectDoesNotExist

from djmoney.money import Money

from common.currency import currency_code_default


def _accumulate_material_cost(build_items):
    """Sum measured/estimated material cost contributions from a list of BuildItem allocations.

    For each allocation, the consumed StockItem's own recorded cost is used if
    available ("measured"); otherwise the underlying component part's cached
    price range is used as a fallback ("estimated").

    Expects `build_items` to already be select_related on at least
    'stock_item', 'stock_item__cost', 'build_line', 'build_line__bom_item' and
    'build_line__bom_item__sub_part' - this function issues at most one
    additional query (a batch PartPricing fetch), regardless of how many
    build_items are passed in.

    Returns:
        A (measured_min, measured_max, estimated_min, estimated_max) tuple.
        Each element is a Money value in the default currency, or None if no
        contribution of that kind was available (as distinct from a contribution
        of zero).
    """
    # Deferred imports to avoid a circular import (build -> pricing -> stock -> build)
    from pricing.models import convert_to_default_currency

    build_items = list(build_items)

    # First pass: resolve each item's own recorded cost (if any), and collect
    # the distinct component parts which will need a price-range fallback -
    # Part.pricing issues its own query per call, so these are batch-fetched
    # afterwards in a single query, rather than once per BuildItem
    resolved = []  # (quantity, min_cost, max_cost, fallback_part_id)
    fallback_part_ids = set()

    for build_item in build_items:
        try:
            item_cost = build_item.stock_item.cost
            min_cost, max_cost = item_cost.min_cost, item_cost.max_cost
        except ObjectDoesNotExist:
            min_cost = max_cost = None

        if min_cost is None and max_cost is None:
            sub_part_id = build_item.build_line.bom_item.sub_part_id
            fallback_part_ids.add(sub_part_id)
            resolved.append((build_item.quantity, None, None, sub_part_id))
        else:
            resolved.append((build_item.quantity, min_cost, max_cost, None))

    pricing_map = {}

    if fallback_part_ids:
        # Deferred import to avoid a circular import (build -> part -> build)
        import part.models

        pricing_map = {
            pricing.part_id: pricing
            for pricing in part.models.PartPricing.objects.filter(
                part_id__in=fallback_part_ids
            )
        }

    currency = currency_code_default()

    measured_min = measured_max = Money(0, currency)
    estimated_min = estimated_max = Money(0, currency)
    has_measured_min = has_measured_max = False
    has_estimated_min = has_estimated_max = False

    for quantity, min_cost, max_cost, fallback_part_id in resolved:
        if fallback_part_id is not None:
            # No recorded cost against the consumed stock item - fall back to
            # the component part's own (cached) price range instead, if available
            sub_part_pricing = pricing_map.get(fallback_part_id)
            min_cost = sub_part_pricing.overall_min if sub_part_pricing else None
            max_cost = sub_part_pricing.overall_max if sub_part_pricing else None
            is_measured = False
        else:
            is_measured = True

        if (converted := convert_to_default_currency(min_cost)) is not None:
            if is_measured:
                measured_min += converted * quantity
                has_measured_min = True
            else:
                estimated_min += converted * quantity
                has_estimated_min = True

        if (converted := convert_to_default_currency(max_cost)) is not None:
            if is_measured:
                measured_max += converted * quantity
                has_measured_max = True
            else:
                estimated_max += converted * quantity
                has_estimated_max = True

    return (
        measured_min if has_measured_min else None,
        measured_max if has_measured_max else None,
        estimated_min if has_estimated_min else None,
        estimated_max if has_estimated_max else None,
    )


def record_output_material_cost(output, allocated_items, user=None):
    """Record material cost against a build output, from its own tracked allocations.

    Called from Build.complete_build_output(), before the provided (tracked,
    per-output) BuildItem allocations are consumed and deleted. Only accounts
    for stock directly allocated to this specific output - see
    `record_pooled_material_cost` for untracked (order-level) allocations.

    Arguments:
        output: The StockItem (build output) being completed
        allocated_items: The BuildItem allocations for this output (install_into=output)
        user: The user completing the output (optional)
    """
    # Deferred imports to avoid a circular import (build -> pricing -> stock -> build)
    import pricing.models
    from pricing.status_codes import CostType

    allocated_items = list(allocated_items)

    if not allocated_items or not output.quantity:
        return

    measured_min, measured_max, estimated_min, estimated_max = (
        _accumulate_material_cost(allocated_items)
    )

    if measured_min is not None or measured_max is not None:
        pricing.models.StockItemCostEntry.objects.set_cost(
            output,
            CostType.MATERIAL.value,
            min_cost=measured_min / output.quantity if measured_min else None,
            max_cost=measured_max / output.quantity if measured_max else None,
            user=user,
        )

    if estimated_min is not None or estimated_max is not None:
        pricing.models.StockItemCostEntry.objects.set_cost(
            output,
            CostType.MATERIAL_ESTIMATED.value,
            min_cost=estimated_min / output.quantity if estimated_min else None,
            max_cost=estimated_max / output.quantity if estimated_max else None,
            user=user,
        )


def record_pooled_material_cost(build, untracked_items, user=None):
    """Amortize pooled (untracked) material cost evenly across every completed output of a build.

    Called from Build.complete_outstanding_allocations(), before the provided
    (untracked, order-level) BuildItem allocations are consumed and deleted.
    This is always an ADDITION to any cost already recorded per-output by
    `record_output_material_cost` for that same output's own tracked
    allocations, not a replacement.

    Splitting a pooled total across outputs by quantity share, then dividing
    each output's share by its own quantity to get a per-unit rate, always
    yields the same per-unit rate for every output - so this is calculated
    once and applied identically to every completed output.

    Arguments:
        build: The Build order being completed
        untracked_items: The untracked (order-level) BuildItem allocations for this build
        user: The user completing the build (optional)
    """
    # Deferred imports to avoid a circular import (build -> pricing -> stock -> build)
    import pricing.models
    from pricing.status_codes import CostType

    untracked_items = list(untracked_items)

    outputs = list(build.complete_outputs)
    total_quantity = sum((output.quantity for output in outputs), start=0)

    if not untracked_items or not outputs or not total_quantity:
        return

    measured_min, measured_max, estimated_min, estimated_max = (
        _accumulate_material_cost(untracked_items)
    )

    for output in outputs:
        if measured_min is not None or measured_max is not None:
            pricing.models.StockItemCostEntry.objects.add_cost(
                output,
                CostType.MATERIAL.value,
                min_cost=measured_min / total_quantity if measured_min else None,
                max_cost=measured_max / total_quantity if measured_max else None,
                user=user,
            )

        if estimated_min is not None or estimated_max is not None:
            pricing.models.StockItemCostEntry.objects.add_cost(
                output,
                CostType.MATERIAL_ESTIMATED.value,
                min_cost=estimated_min / total_quantity if estimated_min else None,
                max_cost=estimated_max / total_quantity if estimated_max else None,
                user=user,
            )
