---
title: Creating a Part
---

## Part Creation Form

New parts can be created from the *Part Category* view, by pressing the *New Part* button:

!!! info "Permissions"
    If the user does not have "create" permission for the *Part* permission group, the *New Part* button will not be available.

{% with id="new", url="part/new_part.png", descript="New Part" %}
{% include "img.html" %}
{% endwith %}


A part creation form is opened as shown below:


{% with id="newform", url="part/part_create_form.png", descript="New Part Form" %}
{% include "img.html" %}
{% endwith %}


Fill out the required part parameters and then press *Submit* to create the new part. If there are any form errors, you must fix these before the form can be successfully submitted.

Once the form is completed, the browser window is redirected to the new part detail page.

### Initial Stock

If the *Create Initial Stock* setting is enabled, then an extra section is available in the part creation form to create an initial quantity of stock for the newly created part:

{% with id="setting", url="part/create_initial_stock_option.png", description="Create stock option" %}
{% include "img.html" %}
{% endwith %}

If this setting is enabled, the following elements are available in the form:

{% with id="initial_stock", url="part/part_initial_stock.png", descript="Initial stock" %}
{% include "img.html" %}
{% endwith %}

Checking the *Create Initial Stock* form input then allows the creation of an initial quantity of stock for the new part.


### Supplier Options

If the part is marked as *Purchaseable*, the form provides some extra options to initialize the new part with manufacturer and / or supplier information:


{% with id="supplierinfo", url="part/part_create_supplier.png", descript="Add supplier information" %}
{% include "img.html" %}
{% endwith %}


If the *Add Supplier Data* option is checked, then supplier part and manufacturer part information can be added to the newly created part:


{% with id="suppliers", url="part/part_new_suppliers.png", descript="Part supplier information" %}
{% include "img.html" %}
{% endwith %}

## Other Part Creation Methods

The following alternative methods for creating parts are supported:

- [Via the REST API](../../api/api)
- [Using the Python library](../../api/python)
- [Within the Admin interface](../../settings/admin)
