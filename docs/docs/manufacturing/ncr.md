---
title: Non-Conformance Reports
---

## Non-Conformance Reports

A *Non-Conformance Report* (NCR) records a quality problem identified against a [Part](../part/index.md) - for example a bad supplier batch, a failed inspection, a customer complaint, or a defect found during a build.

An NCR behaves like a lightweight order - it has a reference number, a status workflow, and can be assigned to a responsible user or group - but its purpose is to *track a problem to closure*, not to move stock or money. Raising an NCR does not automatically affect stock levels, pricing, or any linked order.

!!! tip "Also Known As"
    A Non-Conformance Report may also be referred to as a *Non-Conformity Report*, or simply an *NCR*.

### View Non-Conformance Reports

To navigate to the Non-Conformance Report display, select *Manufacturing* from the main navigation menu, and *Non-Conformances* from the sidebar. This shows a table of all Non-Conformance Reports, which can be filtered to only show the reports you are interested in.

### NCR Permissions

[Permissions](../settings/permissions.md) for Non-Conformance Reports are managed via the `ncr` permission group. Users are assigned appropriate permissions based on the groups they are part of. Note that this is a distinct permission group from `build` - a user does not require any Build Order permissions to view or raise NCRs.

### NCR Status

Each Non-Conformance Report has a specific status code, indicating where it is in its lifecycle:

| Status | Description |
| --- | --- |
| Open | The NCR has been raised, but not yet investigated |
| Investigating | Root cause investigation is underway |
| Dispositioned | A disposition has been decided for all affected stock items |
| Closed | The NCR has been closed out |
| Cancelled | The NCR was raised in error, or withdrawn |

**Source Code**

Refer to the source code for the NCR status codes:

::: build.status_codes.NonConformanceStatus
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []

NCR Status supports [custom states](../concepts/custom_states.md).

!!! info "Status vs. Disposition"
    *Status* tracks where the NCR is in its own lifecycle. *Disposition* - what has been decided about the affected material - is a separate concept, recorded against each individual [linked stock item](#linked-stock-items) rather than the NCR as a whole. See [Item Disposition](#item-disposition) below.

## Create a Non-Conformance Report

From the Non-Conformance Report table, click on <span class='badge inventree add'>{{ icon("plus") }} Report Non-Conformance</span> to open the "Report Non-Conformance" form.

### NCR Reference

Each NCR is uniquely identified by its *Reference* field, automatically generated according to the configured [reference pattern](../settings/reference.md).

### NCR Parameters

The following parameters are available for each NCR, and can be edited by the user:

| Parameter | Description |
| --- | --- |
| Reference | NCR reference e.g. 'NCR-0001' |
| Part | The [part](../part/index.md) against which the non-conformance was raised (required) |
| Description | Description of the non-conformance (required) |
| Severity | Optional severity classification - *Minor*, *Major*, or *Critical* |
| Build Order | Optional link to the [build order](./build.md) which surfaced the problem |
| Sales Order | Optional link to the related [sales order](../sales/sales_order.md) |
| Purchase Order | Optional link to the related [purchase order](../purchasing/purchase_order.md) |
| Return Order | Optional link to the related [return order](../sales/return_order.md) |
| Quantity | Optional affected quantity, as a fact about the world - this is purely informational, and is independent of the quantity recorded against any [linked stock items](#linked-stock-items) |
| Root Cause | Root cause of the problem, typically filled in during investigation |
| Corrective Action | Corrective action taken to resolve the problem |
| Responsible | User (or group of users) responsible for resolving the NCR |
| Target Date | Target date for resolution of the NCR |
| External Link | Link to external webpage |
| Notes | NCR notes, supports markdown |

The part is the only mandatory link - an NCR can be raised with no order context at all (for example, one found during a stocktake or a random audit), or optionally linked to whichever order surfaced the problem.

### Responsible Owner

The NCR can be assigned to a responsible *owner*, which is either a user or a group.

## Non-Conformance Report Detail

Selecting an individual NCR from the table navigates to the NCR detail page, which provides an overview of the report and the available actions.

### Edit NCR

The NCR details can be edited by selecting the {{ icon("edit", color="blue", title="Edit") }} icon under the {{ icon("tools") }} actions menu.

### Linked Stock Items

The *Stock Items* tab lists the [stock items](../stock/index.md) affected by this non-conformance. Stock items can be linked (and unlinked) from this tab.

!!! info "Matching Part Required"
    Only stock items of the same [part](../part/index.md) as the NCR can be linked - the part is the anchor for the whole report, so a mismatched stock item is rejected.

Each linked stock item optionally records an affected *Quantity* (a portion of the stock item, if not all of it is affected) and free-text *Notes*.

#### Item Disposition

Each linked stock item has its own *Disposition*, recording what has been decided for that specific item:

| Disposition | Description |
| --- | --- |
| Pending | No disposition has been decided yet (default value for a newly-linked item) |
| Use As Is | The item is acceptable to use without further action |
| Rework | The item is to be reworked to meet requirements |
| Repair | The item is to be repaired |
| Scrap | The item is to be scrapped |
| Return to Supplier | The item is to be returned to the supplier |

**Source Code**

Refer to the source code for the NCR disposition codes:

::: build.status_codes.NonConformanceDisposition
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []

NCR Disposition supports [custom states](../concepts/custom_states.md).

!!! info "Why Per-Item, Not Per-NCR?"
    A single NCR can cover a batch of material where different units end up with different outcomes - for example, some units might be usable as-is while others need to be scrapped. Recording disposition against each linked stock item (rather than a single value on the NCR itself) allows for this.

Disposition is set by editing a linked stock item directly - it is not a status transition of its own.

### Attachments

File attachments can be uploaded against the NCR, and are displayed in the *Attachments* tab - for example, photos of the defect or supporting inspection documents.

### Notes

NCR notes (which support markdown formatting) are displayed in the *Notes* tab.

## Investigate

To move an NCR into investigation, click the {{ icon("search", title="Investigate") }} *Investigate* button on the NCR detail page. This is available while the NCR is *Open*, and moves it into the *Investigating* status.

## Set Disposition

Once every [linked stock item](#linked-stock-items) has been assigned a [disposition](#item-disposition) other than *Pending*, click the {{ icon("clipboard-check", title="Set Disposition") }} *Set Disposition* button to move the NCR into the *Dispositioned* status.

!!! warning "All Items Must Be Dispositioned"
    If any linked stock item is still at the *Pending* disposition, this action is rejected. An NCR with no linked stock items has nothing to check, and can be dispositioned freely.

This action is available while the NCR is *Open* or *Investigating* - moving into investigation first is optional.

## Close

Once a disposition has been decided, click the {{ icon("circle-check", color="green", title="Close") }} *Close* button to close out the NCR. This is only available once the NCR is in the *Dispositioned* status.

## Cancel

If an NCR was raised in error, or should otherwise be withdrawn, it can be cancelled instead of closed. Click the {{ icon("cancel", color="red", title="Cancel") }} *Cancel* option under the {{ icon("tools") }} actions menu to cancel the NCR. This is available from any open status (*Open*, *Investigating*, or *Dispositioned*).

## Reopen

A *Closed* or *Cancelled* NCR can be reopened, moving it back to the *Open* status. Click the {{ icon("arrow-back", title="Reopen") }} *Reopen* option under the {{ icon("tools") }} actions menu.

## NCR Scheduling

An NCR can optionally be assigned a *Target Date* for resolution. If the target date passes while the NCR is still in an open status (*Open*, *Investigating*, or *Dispositioned*), the NCR is considered *overdue*. This can be useful for tracking NCRs which are behind schedule.

## Non-Conformance Report Reports

Custom [reports](../report/index.md) can be generated against each Non-Conformance Report.

## Non-Conformance Report Settings

The following [global settings](../settings/global.md) are available for adjusting the behavior of Non-Conformance Reports:

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("NCR_REFERENCE_PATTERN") }}
