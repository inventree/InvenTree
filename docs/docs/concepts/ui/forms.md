---
title: Forms
---

## Forms

Data entry and editing within InvenTree is typically performed through the use of forms, which provide a structured interface for inputting and modifying data. Forms are designed to be user-friendly and efficient, allowing users to quickly enter and update information within the system.

Forms are typically displayed as a modal dialog, separated into multiple sections and fields.

### Data Creation

Example: Creating a new part via the "Add Part" form:

{{ image("concepts/ui_form_add_part.png", "Add Part Button") }}

On several forms is displayed option "Keep form open" in bottom part of the form on left side of Submit button (option is visible on the screenshot above). When this switch is turned on, form window is not closed after submit and filled form data is not reset. This is useful for creating more entries at one time with similar properties (e.g. only different number in name).

### Data Editing

Example: Editing an existing purchase order via the "Edit Purchase Order" form:

{{ image("concepts/ui_form_edit_po.png", "Edit Purchase Order") }}

### Confirm Actions

Many actions within InvenTree require user confirmation before they can be executed. This is typically implemented through the use of confirmation dialogs, which prompt the user to confirm their intention before proceeding with the action.

{{ image("concepts/ui_form_hold_po.png", "Confirmation Dialog") }}
