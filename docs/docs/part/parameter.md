---
title: Part Parameters
---

## Part Parameters

A part *parameter* describes a particular "attribute" or "property" of a specific part.

Part parameters are located in the "Parameters" tab, on each part detail page.
There is no limit for the number of part parameters and they are fully customizable through the use of [parameters templates](#parameter-templates).

Here is an example of parameters for a capacitor:

{{ image("part/part_parameters_example.png", "Part Parameters Example") }}

## Parameter Templates

Parameter templates are used to define the different types of parameters which are available for use. The following attributes are defined for a parameter template:

| Attribute | Description |
| --- | --- |
| Name | The name of the parameter template (*must be unique*) |
| Description | Optional description for the template |
| Units | Optional units field (*must be a valid [physical unit](#parameter-units)*) |
| Choices | A comma-separated list of valid choices for parameter values linked to this template. |
| Checkbox | If set, parameters linked to this template can only be assigned values *true* or *false* |
| Selection List | If set, parameters linked to this template can only be assigned values from the linked [selection list](#selection-lists) |

### Create Template

Parameter templates are created and edited via the [settings interface](../settings/global.md).

To create a template:

- Navigate to the "Settings" page
- Click on the "Part Parameters" tab
- Click on the "New Parameter" button
- Fill out the `Create Part Parameter Template` form: `Name` (required) and `Units` (optional) fields
- Click on the "Submit" button.

An existing template can be edited by clicking on the "Edit" button associated with that template:

{{ image("part/parameter_template_edit.png", "Edit Parameter Template") }}

### Create Parameter

After [creating a template](#create-template) or using the existing templates, you can add parameters to any part.

To add a parameter, navigate to a specific part detail page, click on the "Parameters" tab then click on the "New Parameters" button, the `Create Part Parameter` form will be displayed:

{{ image("part/create_part_parameter.png", "Create Part Parameter Form") }}

Select the parameter `Template` you would like to use for this parameter, fill-out the `Data` field (value of this specific parameter) and click the "Submit" button.

## Parametric Tables

Parametric tables gather all parameters from all parts inside a particular [part category](./index.md#part-category) to be sorted and filtered.

To access a category's parametric table, click on the "Parameters" tab within the category view:

{{ image("part/parametric_table_tab.png", "Parametric Table Tab") }}

### Sorting by Parameter Value

The parametric parts table allows the returned parts to be sorted by particular parameter values. Click on the header of a particular parameter column to sort results by that parameter:

{{ image("part/part_sort_by_param.png", "Sort by Parameter") }}

## Parameter Units

The *units* field (which is defined against a [parameter template](#parameter-templates)) defines the base unit of that template. Any parameters which are created against that unit *must* be specified in compatible units.

The in-built conversion functionality means that parameter values can be input in different dimensions - *as long as the dimension is compatible with the base template units*.

!!! info "Read Mode"
    Read more about how InvenTree supports [physical units of measure](../concepts/units.md)

### Incompatible Units

If a part parameter is created with a value which is incompatible with the units specified for the template, it will be rejected:

{{ image("part/part_invalid_units.png", "Invalid Parameter Units") }}

This behaviour can be disabled if required, so that any parameter value is accepted:

{{ image("part/part_parameters_enforce.png", "Enforce Parameter Units") }}

### Parameter Sorting

Parameter sorting takes unit conversion into account, meaning that values provided in different (but compatible) units are sorted correctly:

{{ image("part/part_sorting_units.png", "Sort by Parameter Units") }}

### Selection Lists

Selection Lists can be used to add a large number of predefined values to a parameter template. This can be useful for parameters which must be selected from a large predefined list of values (e.g. a list of standardised colo codes). Choices on templates are limited to 5000 characters, selection lists can be used to overcome this limitation.

It is possible that plugins lock selection lists to ensure a known state.


Administration of lists can be done through the Part Parameter section in the [Admin Center](../settings/admin.md#admin-center) or via the API.
