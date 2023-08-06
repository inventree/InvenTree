---
title: Part Labels
---


## Part Labels

Part label templates are used to generate labels for individual Part instances.

### Creating Part Label Templates

Part label templates are added (and edited) via the admin interface.

### Printing Part Labels

Part label can be printed using the following approaches:

To print a single part label from the Part detail view, select the *Print Label* option.

To print multiple part labels, select multiple parts in the part table and select the *Print Labels* option.

### Context Data

The following context variables are made available to the Part label template:

| Variable | Description |
| -------- | ----------- |
| part | The [Part](../context_variables.md#part) object |
| category | The [Part Category](../context_variables.md#part-category) which contains the Part |
| name | The name of the part |
| description | The description text for the part |
| IPN | Internal part number (IPN) for the part |
| revision | Part revision code |
| qr_data | String data which can be rendered to a QR code |
| parameters | Map (Python dictionary) object containing the parameters associated with the part instance |

#### Parameter Values

The part parameter *values* can be accessed by parameter name lookup in the template, as follows:

```html
{% raw %}

Part: {{ part.name }}
Length: {{ parameters.length }}

{% endraw %}
```

!!! warning "Spaces"
    Note that for parameters which include a `space` character in their name, lookup using the "dot" notation won't work! In this case, try using the [key lookup](../helpers.md#key-access) method:

```html
{% raw %}

Voltage Rating: {% getkey parameters "Voltage Rating" %}
{% endraw %}
```

#### Parameter Data

If you require access to the parameter data itself, and not just the "value" of a particular parameter, you can use the `part_parameter` [helper function](../helpers.md#part-parameters).

For example, the following label template can be used to generate a label which contains parameter data in addition to parameter units:

```html
{% raw %}
{% extends "label/label_base.html" %}

{% load report %}

{% block content %}

{% part_parameter part "Width" as width %}
{% part_parameter part "Length" as length %}

<div>
    Part: {{ part.full_name }}<br>
    Width: {{ width.data }} [{{ width.units }}]<br>
    Length: {{ length.data }} [{{ length.units }}]
</div>

{% endblock content %}
{% endraw %}
```

The following label is produced:

{% with id="report-parameters", url="report/label_with_parameters.png", description="Label with parameters" %}
{% include 'img.html' %}
{% endwith %}
