---
title: Custom Labels
---

## Custom Labels

InvenTree supports printing of custom template-based labels, using the [WeasyPrint](https://weasyprint.org/) PDF generation engine.

Custom labels can be generated using simple HTML templates, with support for QR-codes, and conditional formatting using the Django template engine.


Simple (generic) label templates are supplied 'out of the box' with InvenTree - however support is provided for generation of extremely specific custom labels, to meet any particular requirement.

## Label Templates

Label templates are written using a mixture of [HTML](https://www.w3schools.com/html/) and [CSS](https://www.w3schools.com/css). [Weasyprint](https://weasyprint.org/) templates support a *subset* of HTML and CSS features. In addition to supporting HTML and CSS formatting, the label templates support the Django templating engine, allowing conditional formatting of the label data.

A label template is a single `.html` file which is uploaded to the InvenTree server by the user.

Below is a reasonably simple example of a label template which demonstrates much of the available functionality. The template code shown below will produce the following label:

{% with id="label_example", url="report/label_example.png", description="Example label" %}
{% include 'img.html' %}
{% endwith %}

```html
{% raw %}
<style>
    @page {
        width: 75mm;
        height: 24mm;
        padding: 1mm;
	margin: 0px 0px 0px 0px;
    }

    .location {
        padding: 5px;
        font-weight: bold;
        font-family: Arial, Helvetica, sans-serif;
        height: 100%;
        vertical-align: middle;
        float: right;
        display: inline;
        font-size: 125%;
        position: absolute;
        top: 0mm;
        left: 23mm;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .qr {
        margin: 2px;
        width: 22mm;
        height: 22mm;
    }

</style>
{% load barcode %}
<img class='qr' src="{% qrcode location.format_barcode %}"/>

<div class='location'>
	{{ location.name }}
	<br>
	<br>
	<hr>
	Location ID: {{ location.id }}
	</div>
</div>
{% endraw %}
```

Each significant component of the example template above are described in the sections below:

### Stylesheet

The stylesheet defines the *style* of the label, and is enclosed within the `<style>...</style>` tags. The stylesheet supports any of the CSS features which are supported natively by weasyprint.

Some points of note:

- The `@page` directive specifies the size of the label, and global margins.
- Normal per-class and per-element styling is supported
- Absolute positioning of elements is supported via the `position` CSS directive
- If text is too long to fit on a given label, the `text-overflow` directive can be used

### Context Data

Each label template is supplied with *context data* (variables) which can be used to display information based on the context in which the label is printed. Variables supplied as context objects can be easily rendered to the label using Django templating syntax.

For example, if a StockLocation object is supplied to the label as the variable `location`, it is trivially simple to render the data to the label:

```html
{% raw %}
Location ID: {{ location.id }}
<br>
Location Name: {{ location.name }}
{% endraw %}
```

Refer to the [context variables documentation](./context_variables.md).

### Barcodes

Refer to the [barcode documentation](./barcodes.md).

### Using media files

Refer to the [media files documentation](./helpers.md#media-files).

### Conditional Formatting

Conditional formatting of label data is also supported. Below is an example excerpt from a label which determines the content based on the supplied context variables:

```html
{% raw %}
{% if item.in_stock %}
Quantity: {{ item.quantity }}
{% else %}
OUT OF STOCK
{% endif %}
{% endraw %}
```

### Label Filters

Each label template provides a set of programmable filters which can be used to determine the relevance of that particular label. It may be the case that a particular label template is only applicable if certain conditions are met.

As an example, consider a label template for a StockItem. A user may wish to define a label which displays the firmware version of any items related to the Part with the IPN (Internal Part Number) `IPN123`.

To restrict the label accordingly, we could set the *filters* value to `part__IPN=IPN123`.

## Built-In Templates

The InvenTree installation provides a number of simple *default* templates which can be used as a starting point for creating custom labels. These built-in templates can be disabled if they are not required.

Built-in templates can also be used to quickly scaffold custom labels, using template inheritance.

### Base Template

For example, InvenTree provides a *base* template from which all of the default label templates are derived. This *base* template provides the essentials for generating a label:

```html
{% raw %}
<head>
    <style>
        @page {
            size: {{ width }}mm {{ height }}mm;
            {% block margin %}
            margin: 0mm;
            {% endblock %}
        }

        img {
            display: inline-block;
            image-rendering: pixelated;
        }

        {% block style %}
        {% endblock %}

    </style>
</head>

<body>
    {% block content %}
    <!-- Label data rendered here! -->
    {% endblock %}
</body>

{% endraw %}
```

### Extend Base Template

To extend this template in a custom uploaded label, simply extend as follows:

```html
{% raw %}
{% extends "label/label_base.html" %}

{% block style %}
<!-- You can write custom CSS here -->
{% endblock %}

{% block content %}
<!-- HTML content goes here! -->
{% endblock %}

{% endraw %}
```

## Stock Item Labels

Stock Item label templates are used to generate labels for individual Stock Items.

### Creating Stock Item Label Templates

Stock Item label templates are added (and edited) via the admin interface.

### Printing Stock Item Labels

Stock Item labels can be printed using the following approaches:

To print a single stock item from the Stock Item detail view, select the *Print Label* option as shown below:

{% with id='item_label_single', url='report/label_stock_print_single.png', description='Print single stock item label' %}
{% include 'img.html' %}
{% endwith %}

To print multiple stock items from the Stock table view, select the *Print Labels* option as shown below:

{% with id='item_label_multiple', url='report/label_stock_print_multiple.png', description='Print multiple stock item labels' %}
{% include 'img.html' %}
{% endwith %}

### Context Data

The following variables are made available to the StockItem label template:

| Variable | Description |
| -------- | ----------- |
| item | The [StockItem](./context_variables.md#stockitem) object itself |
| part | The [Part](./context_variables.md#part) object which is referenced by the [StockItem](./context_variables.md#stockitem) object |
| name | The `name` field of the associated Part object |
| ipn | The `IPN` field of the associated Part object |
| revision | The `revision` field of the associated Part object |
| quantity | The `quantity` field of the StockItem object |
| serial | The `serial` field of the StockItem object |
| uid | The `uid` field of the StockItem object |
| tests | Dict object of TestResult data associated with the StockItem |
| parameters | Dict object containing the parameters associated with the base Part |

### URL-style QR code

Stock Item labels support [QR code](./barcodes.md#qr-code) containing the stock item URL, which can be
scanned and opened directly
on a portable device using the camera or a QR code scanner. To generate a URL-style QR code for stock item in the [label HTML template](./labels.md#label-templates), add the
following HTML tag:

``` html
{% raw %}
<img class='custom_qr_class' src='{% qrcode qr_url %}'>
{% endraw %}
```

Make sure to customize the `custom_qr_class` CSS class to define the position of the QR code
on the label.

## Stock Location Labels

Stock Location label templates are used to generate labels for individual Stock Locations.

### Creating Stock Location Label Templates

Stock Location label templates are added (and edited) via the admin interface.

### Printing Stock Location Labels

To print a single label from the Stock Location detail view, select the *Print Label* option.

### Context Data

The following variables are made available to the StockLocation label template:

| Variable | Description |
| -------- | ----------- |
| location | The [StockLocation](./context_variables.md#stocklocation) object itself |

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
| part | The [Part](./context_variables.md#part) object |
| category | The [Part Category](./context_variables.md#part-category) which contains the Part |
| name | The name of the part |
| description | The description text for the part |
| IPN | Internal part number (IPN) for the part |
| revision | Part revision code |
| qr_data | String data which can be rendered to a QR code |
| parameters | Map (Python dictionary) object containing the parameters associated with the part instance |

#### Parameters

The part parameters can be accessed by parameter name lookup in the template, as follows:

```html
{% raw %}

Part: {{ part.name }}
Length: {{ parameters.length }}

{% endraw %}
```

Note that for parameters which include a `space` character in their name, lookup using the "dot" notation won't work! In this case, try using the [key lookup](./helpers.md#key-access) method:

```html
{% raw %}

Voltage Rating: {% getkey parameters "Voltage Rating" %}
{% endraw %}
```
