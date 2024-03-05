---
title: Build Labels
---

## Build Line Labels

Build label templates are used to generate labels for individual build order line items.

### Creating Build Line Label Templates

Build label templates are added (and edited) via the [admin interface](../../settings/admin.md).

### Printing Build Line Labels

Build line labels are printed from the Build Order page, under the *Allocate Stock* tab. Multiple line items can be selected for printing:

{% with id='print_build_labels', url='report/label_build_print.png', description='Print build line labels' %}
{% include 'img.html' %}
{% endwith %}

### Context Data

The following context variables are made available to the Build Line label template:

| Variable | Description |
| --- | --- |
| build_line | The build_line instance |
| build | The build order to which the build_line is linked |
| bom_item | The bom_item to which the build_line is linked |
| part | The required part for this build_line instance. References bom_item.sub_part |
| quantity | The total quantity required for the build line |
| allocated_quantity | The total quantity which has been allocated against the build line |
| allocations | A queryset containing the allocations made against the build_line |

## Example

A simple example template is shown below:

```html
{% raw %}
{% extends "label/label_base.html" %}
{% load barcode report %}
{% load inventree_extras %}

{% block style %}

{{ block.super }}

.label {
  margin: 1mm;
}

.qr {
  height: 28mm;
  width: 28mm;
  position: relative;
  top: 0mm;
  right: 0mm;
  float: right;
}

.label-table {
  width: 100%;
  border-collapse: collapse;
  border: 1pt solid black;
}

.label-table tr {
  width: 100%;
  border-bottom: 1pt solid black;
  padding: 2.5mm;
}

.label-table td {
  padding: 3mm;
}

{% endblock style %}

{% block content %}

<div class='label'>
<table class='label-table'>
  <tr>
    <td>
      <b>Build Order:</b> {{ build.reference }}<br>
      <b>Build Qty:</b> {% decimal build.quantity %}<br>
    </td>
    <td>
      <img class='qr' alt='build qr' src='{% qrcode build.barcode %}'>
    </td>
  </tr>
  <tr>
    <td>
      <b>Part:</b> {{ part.name }}<br>
      {% if part.IPN %}
      <b>IPN:</b> {{ part.IPN }}<br>
      {% endif %}
      <b>Qty / Unit:</b> {% decimal bom_item.quantity %} {% if part.units %}[{{ part.units }}]{% endif %}<br>
      <b>Qty Total:</b> {% decimal quantity %} {% if part.units %}[{{ part.units }}]{% endif %}
    </td>
    <td>
      <img class='qr' alt='part qr' src='{% qrcode part.barcode %}'>
    </td>
  </tr>
</table>
</div>

{% endblock content %}

{% endraw %}
```

Which results in a label like:

{% with id='build_label_example', url='report/label_build_example.png', description='Example build line labels' %}
{% include 'img.html' %}
{% endwith %}
