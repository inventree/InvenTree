---
title: Custom States
---

## Custom States

Several models within InvenTree support the use of *custom states*. Custom states extend the built-in status system by adding extra labels and colours that are displayed in the user interface.

!!! info "Display Only"
    Custom states affect display only — they do not add new workflow steps or change business logic. Every custom state is mapped to an existing built-in state (its *logical key*), and the system uses that built-in state for all decisions such as availability counts, order transitions, and filtering.

### Example

Suppose you want to track stock items that are physically present and available, but are waiting for a quality inspection before use. The built-in `OK` status is the closest match — the item is available — but you want it to appear distinctly in the interface.

You would create a custom state:

- **Logical key**: `OK` — the system treats the item as available stock
- **Label**: `Awaiting Inspection` — shown in the interface instead of "OK"
- **Colour**: `warning` — displayed in amber to draw attention

The item is counted as available stock in all reports and filters, but is visually distinguished from items with a standard `OK` status.

## Managing Custom States

Custom states are managed in the [Admin Center](../settings/admin.md#admin-center) under the *Custom States* section.

!!! warning "Page Reload Required"
    Changes to custom states are only reflected in the user interface after a full page reload.

## State Fields

When creating a custom state, the following fields must be provided:

| Field | Description |
|-------|-------------|
| **Model** | The model type this state applies to (e.g. *Stock Item*, *Build Order*) |
| **Reference Status** | The status class being extended (e.g. `StockStatus`, `BuildStatus`) |
| **Logical Key** | The built-in status value this custom state maps to for business logic |
| **Key** | A unique integer that identifies this custom state in the database |
| **Name** | An uppercase Python identifier for this state (e.g. `AWAITING_INSPECTION`) |
| **Label** | The human-readable text displayed in the interface |
| **Colour** | The badge colour used to display the state |

### Key

The *Key* is the integer value stored in the database when this custom state is active. It must satisfy all of the following:

- Must be a positive integer
- Must not be equal to the *Logical Key*
- Must not conflict with any existing built-in status values for the selected model

### Name

The *Name* field is used internally to identify the state. It must:

- Be uppercase (e.g. `AWAITING_INSPECTION`, not `awaiting_inspection`)
- Be a valid Python identifier (letters, digits, underscores; no spaces or hyphens)
- Not conflict with any existing status names for the selected model

### Colours

The following colour values are available:

| Colour | Appearance |
|--------|------------|
| `primary` | Blue |
| `secondary` | Grey |
| `success` | Green |
| `warning` | Amber |
| `danger` | Red |
| `info` | Cyan |
| `dark` | Dark grey / black |
