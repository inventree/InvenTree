---
title: Creating a Part
---

## Part Creation Form

New parts can be created from the *Part Category* view, by pressing the *New Part* button:

!!! info "Permissions"
    If the user does not have "create" permission for the *Part* permission group, the *New Part* button will not be available.

{{ image("part/new_part.png", "New part") }}


A part creation form is opened as shown below:

{{ image("part/part_create_form.png", "New part form") }}


Fill out the required part parameters and then press *Submit* to create the new part. If there are any form errors, you must fix these before the form can be successfully submitted.

Once the form is completed, the browser window is redirected to the new part detail page.

### Initial Stock

If the *Create Initial Stock* setting is enabled, then an extra section is available in the part creation form to create an initial quantity of stock for the newly created part:

If this setting is enabled, the following elements are available in the form:

{{ image("part/part_initial_stock.png", "Initial stock") }}

Checking the *Create Initial Stock* form input then allows the creation of an initial quantity of stock for the new part.


### Supplier Options

If the part is marked as *Purchaseable*, the form provides some extra options to initialize the new part with manufacturer and / or supplier information:

{{ image("part/part_create_supplier.png", "Part supplier options") }}

If the *Add Supplier Data* option is checked, then supplier part and manufacturer part information can be added to the newly created part:

{{ image("part/part_new_suppliers.png", "Part supplier information") }}

## Other Part Creation Methods

The following alternative methods for creating parts are supported:

- [Via the REST API](../api/index.md)
- [Using the Python library](../api/python/index.md)
- [Within the Admin interface](../settings/admin.md)
