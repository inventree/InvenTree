---
title: Helper Functions
---

Some common functions are provided for use in custom report and label templates. To include these, load the `report` functions at the start of the template:

```html
{% raw %}
<!-- Load the report helper functions -->
{% load report %}
{% endraw %}
```

!!! tip "Use the Source, Luke"
    To see the full range of available helper functions, refer to the source file [report.py](https://github.com/inventree/InvenTree/blob/master/InvenTree/report/templatetags/report.py) where these functions are defined!

## Data Structure Access

A number of helper functions are available for accessing data contained in a particular structure format:

### Index Access

To return the element at a given index in a container which supports indexed access (such as a [list](https://www.w3schools.com/python/python_lists.asp)), use the `getindex` function:

```html
{% raw %}
Item: {% getindex my_list 1 %}
{% endraw %}
```

### Key Access

To return an element corresponding to a certain key in a container which supports key access (such as a [dictionary](https://www.w3schools.com/python/python_dictionaries.asp)), use the `getkey` function:

```html
{% raw %}
<ul>
    {% for key in keys %}
    <li>Key: {% getkey my_container key %}</li>
    {% endfor %}
</ul>
{% endraw %}
```

## Rendering Currency

The helper function `render_currency` allows for simple rendering of currency data. This function can also convert the specified amount of currency into a different target currency:

```html
{% raw %}
{% load report %}

<em>Line Item Unit Pricing:</em>
<ul>
{% for line in order.lines %}
<li>{% render_currency line.price currency=order.supplier.currency %}</li>
{% endfor %}
</ul>

Total Price: {% render_currency order.total_price currency='NZD' decimal_places=2 %}

{% endraw %}
```

The following keyword arguments are available to the `render_currency` function:

| Argument | Description |
| --- | --- |
| currency | Specify the currency code to render in (will attempt conversion if different to provided currency) |
| decimal_places | Specify the number of decimal places to render |
| min_decimal_places | Specify the minimum number of decimal places to render (ignored if *decimal_places* is specified) |
| max_decimal_places | Specify the maximum number of decimal places to render (ignored if *decimal_places* is specified) |
| include_symbol | Include currency symbol in rendered value (default = True) |

## Maths Operations

Simple mathematical operators are available, as demonstrated in the example template below:

```html
{% raw %}
<!-- Load the report helper functions -->
{% load report %}

{% add 1 3 %} <!-- Add two numbers together -->
{% subtract 4 3 %} <!-- Subtract 3 from 4 -->
{% multiply 1.2 3.4 %} <!-- Multiply two numbers -->
{% divide 10 2 %} <!-- Divide 10 by 2 -->

{% endraw %}
```

These operators can also be used with variables:

```html
{% raw %}
{% load report %}

{% for line in order.lines %}
Total: {% multiply line.purchase_price line.quantity %}<br>
{% endfor %}

{% endraw %}
```

## Media Files

*Media files* are any files uploaded to the InvenTree server by the user. These are stored under the `/media/` directory and can be accessed for use in custom reports or labels.

### Uploaded Images

You can access an uploaded image file if you know the *path* of the image, relative to the top-level `/media/` directory. To load the image into a report, use the `{% raw %}{% uploaded_image ... %}{% endraw %}` tag:

```html
{% raw %}
<!-- Load the report helper functions -->
{% load report %}
<img src='{% uploaded_image "subdir/my_image.png" %}'/>
{% endraw %}
```

!!! info "Missing Image"
    If the supplied image filename does not exist, it will be replaced with a placeholder image file

!!! warning "Invalid Image"
    If the supplied file is not a valid image, it will be replaced with a placeholder image file

### Part images

A shortcut function is provided for rendering an image associated with a Part instance. You can render the image of the part using the `{% raw %}{% part_image ... %}{% endraw %}` template tag:

```html
{% raw %}
<!-- Load the report helper functions -->
{% load report %}
<img src='{% part_image part %}'/>
{% endraw %}
```

### Company Images

A shortcut function is provided for rendering an image associated with a Company instance. You can render the image of the company using the `{% raw %}{% company_image ... %}{% endraw %}` template tag:

```html
{% raw %}
<!-- Load the report helper functions -->
{% load report %}
<img src='{% company_image company %}'/>
{% endraw %}
```

## InvenTree Logo

A template tag is provided to load the InvenTree logo image into a report. You can render the logo using the `{% raw %}{% logo_image %}{% endraw %}` tag:

```html
{% raw %}
{% load report %}
<img src='{% logo_image %}'/>
{% endraw %}
```

### Custom Logo

If the system administrator has enabled a [custom logo](../start/config.md#customisation-options), then this logo will be used instead of the base InvenTree logo.

This is a useful way to get a custom company logo into your reports.

If you have a custom logo, but explicitly wish to load the InvenTree logo itself, add `custom=False` to the tag:

```html
{% raw %}
{% load report %}
<img src='{% logo_image custom=False %}'/>
{% endraw %}
```

## Report Assets

[Report Assets](./report.md#report-assets) are files specifically uploaded by the user for inclusion in generated reports and labels.

You can add asset images to the reports and labels by using the `{% raw %}{% asset ... %}{% endraw %}` template tag:

```html
{% raw %}
<!-- Load the report helper functions -->
{% load report %}
<img src="{% asset 'my_awesome_logo.png' %}"/>
{% endraw %}
```
