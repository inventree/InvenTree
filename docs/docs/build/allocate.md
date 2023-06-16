---
title: Build Allocation
---

## Build Allocation

Allocating stock items to a build order signals an intent that those stock items will be removed from the InvenTree database once the build order is completed.

Depending on the particular requirements of the build, and your stock control setup, allocating stock items to a build can be a complex task. In this regard, InvenTree provides an allocation interface which attempts to keep the number of user interactions required to a minimum.

!!! warning "Build Completion"
    Marking a build as *complete* will remove allocated items from stock. This operation cannot be reversed, so take care!

### Untracked vs Tracked Stock

Before continuing, it is important that the difference between *untracked* and *tracked* parts, as they impose different requirements when it comes to stock allocation.

#### Untracked Stock

*Untracked* stock items are consumed against the build order, once the order is completed. When a build order is completed, any allocated stock items which are not [trackable](../part/trackable.md) are marked as *consumed*. These items remain in the InvenTree database, but are unavailable for use in any stock operations.

!!! info "Example: Untracked Parts"
    You require 15 x 47K resistors to make a batch of PCBs. You have a reel of 1,000 resistors which you allocate to the build. At completion of the build, the available stock quantity is reduced to 985.

#### Tracked Stock

[Tracked](../part/trackable.md) stock items, on the other hand, require special attention. These are parts which we wish to track against specific [build outputs](./output.md). When the build order is completed, *tracked* stock items are installed *within* the assembled build output.

!!! info "Example: Tracked Parts"
    The assembled PCB (in the example above) is a *trackable* part, and is given a serial number #001. The PCB is then used to make a larger assembly in a subsequent build order. At the completion of that build order, the tracked PCB is *installed* in the assembly.

#### BOM Considerations

A [Bill of Materials](./bom.md) to generate an assembly may consist of a mixture of *untracked* and *tracked* components. The build order process can facilitate this, as documentated in the sections below.

### Tracked Build Outputs

If a Build Order is created for an assembled part which is itself designed as *trackable*, some extra restrictions apply:

- Build outputs must be single quantity
- Build outputs must be serialized as they are created

## Allocating Untracked Stock

Untracked stock items are allocated against the *Build Order* itself. We do not need to track which *Build Output* these items will be installed into, and so the allocation process can be simplified.

Navigate to the *Allocate Stock* tab to view the stock allocation table:

{% with id="build_allocate_detail", url="build/build_allocate_detail.png", description="Allocate stock" %}
{% include "img.html" %}
{% endwith %}

In this example, there are two BOM line items which have been partially allocated to the build. Each line has a progress bar indicating how much of the required stock has been allocated.

In each row, pressing the <span class='fas fa-plus'></span> icon expands the row, showing a list of stock items which have been allocated against this build.

!!! info "Multiple Allocations"
    Note that multiple stock items can be allocated to the given BOM line, if a single stock item does not have sufficient stock

{% with id="build_allocation_expand", url="build/build_allocation_expand.png", description="Allocate expand" %}
{% include "img.html" %}
{% endwith %}

## Manual Stock Allocation

For each line in the BOM, stock will be automatically allocated if one (and only one) stock item (for the referenced part) is found (within the specified *source location* for the build):

Selecting *Allocate Stock* opens a dialog window which displays the stock items which will be allocated to the build during the auto allocation process:

{% with id="build_auto", url="build/build_auto_allocate.png", description="Auto allocate" %}
{% include "img.html" %}
{% endwith %}

Note here that there are two parts in the BOM which can be automatically allocated, as they only have a single corresponding StockItem available.
However the other BOM line item exists in multiple locations, and thus cannot be automatically allocated. These will need to be manually selected by the user.

### Row Allocation

Stock can be manually allocated to the build as required, using the *Allocate stock* button available in each row of the allocation table

### Edit Allocations

Stock allocations can be manually adjusted or deleted using the action buttons available in each row of the allocation table.

### Deallocate Stock

The *Deallocate Stock* button can be used to remove all allocations of untracked stock items against the build order.

## Automatic Stock Allocation

To speed up the allocation process, the *Auto Allocate* button can be used to allocate untracked stock items to the build. Automatic allocation of stock items does not work in every situation, as a number of criteria must be met.

The *Automatic Allocation* dialog is presented as shown below:

{% with id="auto_allocate_dialog", url="build/auto_allocate_dialog.png", description="Automatic allocation dialog" %}
{% include "img.html" %}
{% endwith %}

**Source Location**

Select the master location where stock items are to be allocated from. Leave this input blank to allocate stock items from any available location.

**Interchangeable Stock**

Set this option to *True* to signal that stock items can be used interchangeably. This means that in the case where multiple stock items are available, the auto-allocation routine does not care which stock item it uses.

!!! warning "Take Care"
    If the *Interchangeable Stock* option is enabled, and there are multiple stock items available, the results of the automatic allocation algorithm may somewhat unexpected.

!!! info "Example"
    Let's say that we have 5 reels of our *C_100nF_0603* capacitor, each with 4,000 parts available. If we do not mind which of these reels the stock should be taken from, we enable the *Interchangeable Stock* option in the dialog above. In this case, the stock will be allocated from one of these reels, and eventually subtracted from stock when the build is completed.

**Substitute Stock**

Set this option to *True* to allow substitute parts (as specified by the BOM) to be allocated, if the primary parts are not available.

## Allocating Tracked Stock

Allocation of tracked stock items is slightly more complex. Instead of being allocated against the *Build Order*, tracked stock items must be allocated against an individual *Build Output*.

Allocating tracked stock items to particular build outputs is performed in the *Pending Items* tab:

In the *Pending Items* tab, we can see that each build output has a stock allocation requirement which must be met before that build output can be completed:

{% with id="build_allocate_tracked_parts", url="build/build_allocate_tracked_parts.png", description="Allocate tracked parts" %}
{% include "img.html" %}
{% endwith %}

Here we can see that the incomplete build outputs (serial numbers 15 and 14) now have a progress bar indicating the status of tracked stock item allocation:

- Serial number 15 has been fully allocated, and can be completed
- Serial number 14 has not been fully allocated, and cannot yet be completed

### Allocated Stock

*Tracked* stock items which are allocated against the selected build output will be removed from stock, and installed "inside" the output assembly. The allocated stock items will still exist in the InvenTree database, however will no longer be available for regular stock actions.

!!! note "Example: Tracked Stock"
    Let's say we have 5 units of "Tracked Part" in stock - with 1 unit allocated to the build output. Once we complete the build output, there will be 4 units of "Tracked Part" in stock, with 1 unit being marked as "installed" within the assembled part

## Completing a Build

!!! warning "Complete Build Outputs"
    A build order cannot be completed if there are outstanding build outputs. Ensure that all [build outputs](./output.md) are completed first.

Once all build outputs have been completed, the build order itself can be completed by selecting the *Complete Build* button:

{% with id="build_complete", url="build/complete_build.png", description="Complete build order" %}
{% include "img.html" %}
{% endwith %}

### Allocated Stock

All *untracked* stock items which are allocated against this build will be removed from stock, and *consumed* by the build order. These consumed items can be later viewed in the [consumed stock tab](./build.md#consumed-stock).
