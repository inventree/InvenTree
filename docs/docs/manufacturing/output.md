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

{{ image("build/build_outputs_incomplete.png", "Incomplete build outputs") }}

### Completed Outputs

The *Completed Outputs* tab displays any [completed](#complete-build-output) or [scrapped](#scrap-build-output) outputs for the current build order.

{{ image("build/build_outputs_complete.png", "Completed build outputs") }}

## Create Build Output

Create a new build output by pressing the <span class="badge inventree add">{{ icon("plus-circle") }} New Build Output</span> button under the [incomplete outputs](#incomplete-outputs) tab:

{{ image("build/build_output_create.png", "Create build output") }}

### Create Options

The following options are available when creating a new build output:

| Option | Description |
| --- | --- |
| Quantity | The number of items to create as part of this build output |
| Serial Numbers | Optional serial numbers for the generated outputs - see [below](#creating-outputs-without-serial-numbers) for when this field may be left blank |
| Batch Code | Batch code identifier for the generated output(s) |
| Auto Allocate Serial Numbers | If selected, any available tracked subcomponents which already have serial numbers assigned, will be automatically assigned to matching build outputs |

### Specifying Serial Numbers

Refer to the [serial number generation guide](../stock/tracking.md#generating-serial-numbers) for further information on serial number input.

### Creating Outputs Without Serial Numbers

Serial numbers are not required when creating a build output, even if the part being built is marked as [trackable](../part/trackable.md). This allows a batch quantity to be produced up-front - for example, a quantity of PCBs which will not be individually serialized until later in the manufacturing process, or units received into an [external build order](./external.md) which are not yet serialized.

If the *Serial Numbers* field is left blank, a single build output is created with the specified *Quantity*, rather than one output per unit. This output remains a single (non-serialized) [stock item](../stock/index.md), which can be serialized at a later stage - for example, by splitting it into individual units and assigning serial numbers - before it is [completed](#complete-build-output).

!!! note "Tracked BOM Items"
    If the [Bill of Materials](./bom.md) for the assembled part contains tracked sub-components, serial numbers are still required when creating build outputs - see [tracked build outputs](./allocate.md#tracked-build-outputs) for further information.

## Complete Build Output

*Completing* a build output marks that output as finished, in the context of the given build order.

An individual build output is completed by selecting the "Complete build output" button associated with that build output:

{{ image("build/build_output_complete.png", "Complete build output") }}

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
| Location | The [stock location](../stock/index.md#stock-location) where the outputs will be located |
| Notes | Any additional notes associated with the completion of these outputs |
| Accept Incomplete Allocation | If selected, this option allows [tracked build outputs](./allocate.md#tracked-build-outputs) to be completed in the case where required BOM items have not been fully allocated |

### Partial Completion

A build output may be *partially completed* by specifying a quantity less than the total quantity of that build output. In such a case, the following actions are performed:

- The incomplete build output is "split" into two separate build outputs
- The specified quantity is marked as completed, and the completed build quantity is increased accordingly
- The remaining quantity is left as an incomplete build output, available for future completion

!!! note "Serialized Outputs"
    Serialized build outputs cannot be partially completed.


## Scrap Build Output

*Scrapping* a build output marks the particular output as rejected, in the context of the given build order.

An individual build output is completed by selecting the *Scrap build output* button associated with that build output:

{{ image("build/build_output_scrap.png", "Scrap build output") }}

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

### Partial Scrapping

A build output may be *partially scrapped* by specifying a quantity less than the total quantity of that build output. In such a case, the following actions are performed:

- The incomplete build output is "split" into two separate build outputs
- The specified quantity is marked as scrapped, and the completed build quantity is *not* increased
- The remaining quantity is left as an incomplete build output, available for future completion

!!! note "Serialized Outputs"
    Serialized build outputs cannot be partially scrapped.

## Cancel Build Output

*Cancelling* a build output causes the build output to be deleted, and removed from the database entirely. Use this option when the build output does not physically exist (or was never built) and should not be tracked in the database.

{{ image("build/build_output_delete.png", "Cancel build output") }}

Marking the build output(s) as cancelled performs the following actions:

- Any allocated stock items are returned to stock
- The build output is removed from the database
