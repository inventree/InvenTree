---
title: Part Parameters
---

## Part Parameters

Part parameters are located in the "Parameters" tab, on each part detail page.
There is no limit for the number of part parameters and they are fully customizable through the use of parameters templates.

Here is an example of parameters for a capacitor:
{% with id="part_parameters_example", url="part/part_parameters_example.png", description="Part Parameters Example List" %}
{% include 'img.html' %}
{% endwith %}

### Create Template

A *Parameter Template* is required for each part parameter.

To create a template:

- navigate to the "Settings" page
- click on the "Parts" tab
- scroll down to the "Part Parameter Templates" section
- click on the "New Parameter" button
- fill out the `Create Part Parameter Template` form: `Name` (required) and `Units` (optional) fields
- finally click on the "Submit" button.

### Create Parameter

After [creating a template](#create-template) or using the existing templates, you can add parameters to any part.

To add a parameter, navigate to a specific part detail page, click on the "Parameters" tab then click on the "New Parameters" button, the `Create Part Parameter` form will be displayed:

{% with id="create_part_parameter", url="part/create_part_parameter.png", description="Create Part Parameter Form" %}
{% include 'img.html' %}
{% endwith %}

Select the parameter `Template` you would like to use for this parameter, fill-out the `Data` field (value of this specific parameter) and click the "Submit" button.

### Parametric Tables

Parametric tables gather all parameters from all parts inside a category to be sorted and filtered.

To access a category's parametric table, click on the "Parameters" tab within the category view:

{% with id="parametric_table_tab", url="part/parametric_table_tab.png", description="Parametric Table Tab" %}
{% include 'img.html' %}
{% endwith %}

Below is an example of capacitor parametric table filtered with `Package Type = 0402`:

{% with id="parametric_table_example", url="part/parametric_table_example.png", description="Parametric Table Example" %}
{% include 'img.html' %}
{% endwith %}
