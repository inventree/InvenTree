---
title: Build Orders
---

## Build Orders

A *Build Order* is used to create new stock by assembling component parts, according to a [Bill of Materials](./bom.md) (BOM).

A BOM can be specified for any [Part](../part/part.md) which is designated as an *Assembly*. The BOM consists of other Parts which are designated as *Components*.

A *Build Order* uses the BOM to allocate stock items to the assembly process. As the *Build Order* is completed, the required stock quantities are subtracted from allocated stock items.

### View Build Orders

To navigate to the Build Order display, select *Build* from the main navigation menu:

{% with id="build_display", url="build/build_display.png", description="Display Builds" %}
{% include "img.html" %}
{% endwith %}

#### Table View

*Table View* provides a table of Build Orders, which can be filtered to only show the orders you are interested in.

{% with id="build_list", url="build/build_list.png", description="Build List" %}
{% include "img.html" %}
{% endwith %}

#### Calendar View

*Calendar View* shows a calendar display with upcoming build orders, based on the various dates specified for each build.

## Build Order Details

### Build Order Reference

Each Build Order is uniquely identified by its *Reference* field. Read more about [reference fields](../settings/reference.md).

### Build Parameters

The following parameters are available for each Build Order, and can be edited by the user:

| Parameter | Description |
| --- | --- |
| Reference | Build Order reference e.g. '001' |
| Description | Description of the Build Order |
| Part | Link to the *Part* which will be created from the Build Order |
| Quantity | Number of stock items which will be created from this build |
| Sales Order | Link to a *Sales Order* to which the build outputs will be allocated |
| Source Location | Stock location to source stock items from (blank = all locations) |
| Destination Location | Stock location where the build outputs will be located |
| Start Date | The scheduled start date for the build |
| Target Date | Target date for build completion |
| Responsible | User (or group of users) who is responsible for the build |
| External Link | Link to external webpage |
| Notes | Build notes, supports markdown |

### Build Output

A *Build Output* creates a new stock instance of the assembly part, of a specified quantity. Each *Build Order* requires at least one build output. Multiple build outputs can be specified if the build is completed in batches.

Read more about build outputs [here](./output.md).

### Build Status

Each *Build Order* has an associated *Status* flag, which indicates the state of the build:

| Status | Description |
| ----------- | ----------- |
| `Pending` | Build order has been created, but is not yet in production |
| `Production` | Build order is currently in production |
| `On Hold` | Build order has been placed on hold, but is still active |
| `Cancelled` | Build order has been cancelled |
| `Completed` | Build order has been completed |

**Source Code**

Refer to the source code for the Build Order status codes:

::: build.status_codes.BuildStatus
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []

### Stock Allocations

When a *Build Order* is created, we then have the ability to *allocate* stock items against that build order. The particular parts we need to allocate against the build are specified by the BOM for the part we are assembling.

- A *Stock Allocation* links a certain quantity of a given *Stock Item* to the build.
- At least one stock allocation is required for each line in the BOM
- Multiple stock allocations can be made against a BOM line if a particular stock item does not have sufficient quantity for the build

!!! info "Example - Stock Allocation"
	Let's say that to assembly a single "Widget", we require 2 "flanges". So, to complete a build of 10 "Widgets", 20 "flanges" will be required. We *allocate* 20 flanged against this build order.

Allocating stock to a build does not actually subtract the stock from the database. Allocations signal an *intent* to take that stock for the purpose of this build. Stock allocations are subtracted from stock at the completion of a build.

!!! info "Part Allocation Information"
    Any part which has stock allocated to a build order will indicate this on the part information page.

For further information, refer to the [stock allocation documentation](./allocate.md).

## Build Order Display

The detail view for a single build order provides multiple display panels, as follows:

### Build Details

The *Build Details* panel provides an overview of the Build Order:

{% with id="build_details", url="build/build_panel_details.png", description="Build details panel" %}
{% include "img.html" %}
{% endwith %}

### Line Items

The *Line Items* panel displays all the line items (as defined by the [bill of materials](./bom.md)) required to complete the build order.

{% with id="build_allocate", url="build/build_panel_line_items.png", description="Build line items panel" %}
{% include "img.html" %}
{% endwith %}

The allocation table (as shown above) provides an interface to allocate required stock, and also shows the stock allocation progress for each line item in the build.

### Incomplete Outputs

The *Incomplete Outputs* panel shows the list of in-progress [build outputs](./output.md) (created stock items) associated with this build.

{% with id="build_outputs", url="build/build_outputs.png", description="Outputs tab" %}
{% include "img.html" %}
{% endwith %}

!!! info "Example: Build Outputs"
	In the example image above, a single output (serial number 2) has been completed, while serial numbers 1 and 4 are still in progress.

- Build outputs can be created from this screen, by selecting the *Create New Output* button
- Outputs which are "in progress" can be completed or cancelled
- Completed outputs (which are simply *stock items*) can be viewed in the stock table at the bottom of the screen

### Completed Outputs

This panel displays all the completed build outputs (stock items) which have been created by this build order:

### Allocated Stock

The *Allocated Stock* tab displays all stock items which have been *allocated* to this build order. These stock items are reserved for this build, and will be consumed when the build is completed:

{% with id="allocated_stock_table", url="build/allocated_stock_table.png", description="Allocated Stock Table" %}
{% include "img.html" %}
{% endwith %}

### Consumed Stock

The *Consumed Stock* tab displays all stock items which have been *consumed* by this build order. These stock items remain in the database after the build order has been completed, but are no longer available for use.

- [Tracked stock items](./allocate.md#tracked-stock) are consumed by specific build outputs
- [Untracked stock items](./allocate.md#untracked-stock) are consumed by the build order

### Child Builds

If there exist any build orders which are *children* of the selected build order, they are displayed in the *Child Builds* tab:

{% with id="build_childs", url="build/build_childs.png", description="Child builds panel" %}
{% include "img.html" %}
{% endwith %}

### Test Results

For *trackable* parts, test results can be recorded against each build output. These results are displayed in the *Test Results* panel:

{% with id="build_test_results", url="build/build_panel_test_results.png", description="Test Results panel" %}
{% include "img.html" %}
{% endwith %}

This table provides a summary of the test results for each build output, and allows test results to be quickly added for each build output.

### Test Statistics

For *trackable* parts, this panel displays a summary of the test results for all build outputs:

{% with id="build_test_stats", url="build/build_panel_test_statistics.png", description="Test Statistics panel" %}
{% include "img.html" %}
{% endwith %}

### Attachments

Files attachments can be uploaded against the build order, and displayed in the *Attachments* tab:

{% with id="build_attachments", url="build/build_attachments.png", description="Attachments tab" %}
{% include "img.html" %}
{% endwith %}

### Notes

Build order notes (which support markdown formatting) are displayed in the *Notes* tab:

{% with id="build_notes", url="build/build_notes.png", description="Notes tab" %}
{% include "img.html" %}
{% endwith %}

## Create Build Order

To create a build order for your part, you have two options:

### Part Detail Page

- Navigate to the detail page for the assembly part you wish to create
- Select the *Build Orders* tab
- Select *Start new Build*

{% with id="build_create_from_part", url="build/build_create_from_part.png", description="Create build from Part view" %}
{% include "img.html" %}
{% endwith %}

### Build Order Page

- Navigate to the Build Order overview page
- Click on *New Build Order*

Fill-out the form as required, then click the "Submit" button to create the build.

### Create Child Builds

When creating a new build order, you have the option to automatically generate build orders for any subassembly parts. This can be useful to create a complete tree of build orders for a complex assembly. *However*, it must be noted that any build orders created for subassemblies will use the default BOM quantity for that part. Any child build orders created in this manner must be manually reviewed, to ensure that the correct quantity is being built as per your production requirements.

## Complete Build Order

To complete a build, click on <span class='fas fa-tools'></span> icon on the build detail page, the `Complete Build` form will be displayed.

The form will validate the build order is ready to be completed, and will prevent you from continuing if any of the below conditions are present unless you select one of the presented options to override the validation and accept completion of the build anyway.

!!! info "Incomplete Build"
	If the warning message `Required build quantity has not been completed` is shown, you have build outputs that have not yet been completed.

	In the unlikely event that you wish to proceed despite this, you can toggle the `Accept Incomplete` option to true to override the error and allow completion without the required number of build outputs.

!!! info "Incomplete Allocation"
	If the warning message `Require stock has not been fully allocated` is shown, make sure to allocate stock matching all BOM items to the build before proceeding with build completion.

	If you wish to complete the build despite the missing parts, toggle the `Accept Unallocated` option to true to override the warning and allow completion with unallocated parts.

!!! info "Overallocated Stock Items"
	If the warning message `Some stock items have been overallocated` is shown, you have more stock than required by the BOM for the part being built allocated to the build order. By default the `Not permitted` option is selected and you will need to return to the allocation screen and remove the extra items before the build can be completed.

	Alternatively, you can select `Accept as consumed by this build order` to continue with the allocation and remove the extra items from stock (e.g. if they were destroyed during build), or select `Deallocate before completing this build order` if you would like the extra items to be returned to stock for use in future builds.


Select a `Location` to store the resulting parts from the build then click on the confirmation switch.
Finally, click on the "Complete Build" button to process the build completion.

!!! warning "Completed Build"
	**A completed build cannot be re-opened**. Make sure to use the confirm only if you are certain that the build is complete.

## Cancel Build Order

To cancel a build, click on <span class='fas fa-times-circle'></span> icon on the build detail page.

The `Cancel Build` form will be displayed, click on the confirmation switch then click on the "Cancel Build" button to process the build cancellation.

!!! warning "Cancelled Build"
	**A cancelled build cannot be re-opened**. Make sure to use the cancel option only if you are certain that the build won't be processed.

## Build Scheduling

Build orders can be scheduled for a future date, to allow for planning of production schedules.

### Start Date

Build orders can be optionally scheduled to *start* at a specified date, by setting the *Start Date* field. This field can be left blank if the build is to start immediately.

### Target Date

Build orders can be optionally scheduled to be completed by a certain date, by setting the *Target Date* field. This field can be left blank if the build has no specific deadline.

### Overdue Builds

If the *Target Date* is reached but the build order remains incomplete, then the build is considered *overdue*.

This can be useful for tracking production delays, and can be used to generate reports on build order performance.

## Build Order Settings

The following [global settings](../settings/global.md) are available for adjusting the behavior of build orders:

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("BUILDORDER_REFERENCE_PATTERN") }}
{{ globalsetting("BUILDORDER_REQUIRE_RESPONSIBLE") }}
{{ globalsetting("BUILDORDER_REQUIRE_ACTIVE_PART") }}
{{ globalsetting("BUILDORDER_REQUIRE_LOCKED_PART") }}
{{ globalsetting("BUILDORDER_REQUIRE_VALID_BOM") }}
{{ globalsetting("BUILDORDER_REQUIRE_CLOSED_CHILDS") }}
{{ globalsetting("PREVENT_BUILD_COMPLETION_HAVING_INCOMPLETED_TESTS") }}
