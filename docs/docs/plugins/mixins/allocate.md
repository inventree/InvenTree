---
title: Allocate Mixin
---

## AllocateMixin

The `AllocateMixin` class enables plugins to customize how stock items are automatically allocated against [build orders](../../manufacturing/build.md) and [sales orders](../../sales/sales_order.md).

When a user triggers "auto allocation" of stock against an order, InvenTree first determines a list of candidate stock items for each line, using the default allocation rules (e.g. in-stock, matching part / variant / substitute, location, serialization, etc). Before this candidate list is used to actually create the stock allocations, it is passed through any active plugins which implement the `AllocateMixin` class - allowing a plugin to filter, reorder, or otherwise adjust which stock items are used.

!!! info "Multi Plugin Support"
    If multiple plugins are active which implement the `AllocateMixin` methods, they are called in turn - each plugin receives the (possibly already adjusted) output of the previous plugin.

!!! info "Default Behavior"
    Neither method needs to be implemented by a plugin. If a method is not overridden - or if it returns `None` - the provided list of stock items is passed through unmodified.

### Build Order Allocation

The `filter_build_allocation` method is called when automatically allocating stock against a [build order](../../manufacturing/build.md) - for both "tracked" and "untracked" stock items.

Note that this method is called *once per candidate list* - once for each `BuildLine` (untracked stock), and once for each tracked build output.

::: plugin.base.integration.AllocateMixin.AllocateMixin.filter_build_allocation
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      extra:
        show_source: True
      summary: False
      members: []

### Sales Order Allocation

The `filter_sales_order_allocation` method is called when automatically allocating stock against a [sales order](../../sales/sales_order.md).

::: plugin.base.integration.AllocateMixin.AllocateMixin.filter_sales_order_allocation
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      extra:
        show_source: True
      summary: False
      members: []

### Sample Plugin

A sample plugin which implements custom allocation filtering is provided in the InvenTree source code. It excludes any stock item with a batch code of `REJECT` from being automatically allocated:

::: plugin.samples.integration.allocate_sample.SampleAllocatePlugin
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []
