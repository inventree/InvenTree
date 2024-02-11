---
title: Build Outputs
---

## Build Outputs

With reference to a [build order](./build.md), a *Build Output* is a finished product which is expected to be produced by completing the order.

- A single build order may have multiple build outputs which are produced at different times or by different operators.
- An individual build output may be a single unit, or a batch of units
- Serial numbers and batch codes can be associated with a build output

### Incomplete Outputs

The *Incomplete Outputs* tab displays any outstanding / in-progress build outputs for the current build order.

{% with id="build-outputs-incomplete", url="build/build_outputs_incomplete.png", description="Incomplete build outputs" %}
{% include "img.html" %}
{% endwith %}

### Completed Outputs

The *Completed Outputs* tab displays any [completed](#complete-build-output) or [scrapped](#scrap-build-output) outputs for the current build order.

{% with id="build-outputs-complete", url="build/build_outputs_complete.png", description="Complete build outputs" %}
{% include "img.html" %}
{% endwith %}

## Create Build Output

Create a new build output by pressing the <span class="badge inventree add"><span class='fas fa-plus-circle'></span> New Build Output</span> button under the [incomplete outputs](#incomplete-outputs) tab:

{% with id="build_output_create", url="build/build_output_create.png", description="Create build output" %}
{% include "img.html" %}
{% endwith %}

### Create Options

The following options are available when creating a new build output:

| Option | Description |
| --- | --- |
| Quantity | The number of items to create as part of this build output |
| Serial Numbers | If this is a tracked build output, the serial numbers for each of the generated outputs |
| Batch Code | Batch code identifier for the generated output(s) |
| Auto Allocate Serial Numbers | If selected, any available tracked subcomponents which already have serial numbers assigned, will be automatically assigned to matching build outputs |

### Specifying Serial Numbers

Refer to the [serial number generation guide](../stock/tracking.md#generating-serial-numbers) for further information on serial number input.

## Complete Build Output

*Completing* a build output marks that output as finished, in the context of the given build order.

An individual build output is completed by selecting the "Complete build output" button associated with that build output:

{% with id="build_output_complete", url="build/build_output_complete.png", description="Complete build output" %}
{% include "img.html" %}
{% endwith %}

Here the user can select the destination location for the build output, as well as the stock item status.

Marking the build output(s) as complete performs the following actions:

- The completed build quantity is increased by the quantity of the selected build output(s)
- The build output(s) are marked as "completed", and available for stock actions
- Any [tracked BOM items](./allocate.md#allocating-tracked-stock) which are allocated to the build output are *installed* into that build output.

### Complete Options

The following options are available when completing a build output:

| Option | Description |
| --- | --- |
| Status | The [stock status](../stock/status.md) for the completed outputs |
| Location | The [stock location](../stock/stock.md#stock-location) where the outputs will be located |
| Notes | Any additional notes associated with the completion of these outputs |
| Accept Incomplete Allocation | If selected, this option allows [tracked build outputs](./allocate.md#tracked-build-outputs) to be completed in the case where required BOM items have not been fully allocated |

## Scrap Build Output

*Scrapping* a build output marks the particular output as rejected, in the context of the given build order.

An individual build output is completed by selecting the *Scrap build output* button associated with that build output:

{% with id="build_output_scrap", url="build/build_output_scrap.png", description="Scrap build output" %}
{% include "img.html" %}
{% endwith %}

Marking the build output(s) as scrapped performs the following actions:

- The build outputs are marked as "rejected" and removed from the build
- The completed build quantity *does not increase*
- The build outputs are not available for any further stock actions
- Optionally, any [tracked BOM items](./allocate.md#allocating-tracked-stock) which are allocated to the build output are *installed* into the rejected build output

### Scrap Options

The following options are available when scrapping a build order:

| Option | Description |
| --- | --- |
| Location | The stock location where the scrapped build output(s) will be located |
| Notes | Any additional notes associated with the scrapping of these outputs |
| Discard Allocations | If selected, any installed BOM items will be removed first, before marking the build output as scrapped. Use this option if the installed items are recoverable and can be used elsewhere |

## Delete Build Output

*Deleting* a build output causes the build output to be cancelled, and removed from the database entirely. Use this option when the build output does not physically exist (or was never built) and should not be tracked in the database.

{% with id="build_output_delete", url="build/build_output_delete.png", description="Delete build output" %}
{% include "img.html" %}
{% endwith %}

Marking the build output(s) as deleted performs the following actions:

- Any allocated stock items are returned to stock
- The build output is removed from the database
