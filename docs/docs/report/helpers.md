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
    To see the full range of available helper functions, refer to the source file [report.py](https://github.com/inventree/InvenTree/blob/master/src/backend/InvenTree/report/templatetags/report.py) where these functions are defined!

## Assigning Variables

When making use of helper functions within a template, it can be useful to store the result of the function to a variable, rather than immediately rendering the output.

For example, using the [render_currency](#rendering-currency) helper function, we can store the output to a variable which can be used at a later point in the template:

```html
{% raw %}

{% load report %}

{% render_currency 12.3 currency='USD' as myvar %}
...
...
Result: {{ myvar }}

{% endraw %}
```

## Data Structure Access

A number of helper functions are available for accessing data contained in a particular structure format:

### Index Access

To return the element at a given index in a container which supports indexed access (such as a [list](https://www.w3schools.com/python/python_lists.asp)), use the `getindex` function:

```html
{% raw %}
{% getindex my_list 1 as value %}
Item: {{ value }}
{% endraw %}
```

### Key Access

To return an element corresponding to a certain key in a container which supports key access (such as a [dictionary](https://www.w3schools.com/python/python_dictionaries.asp)), use the `getkey` function:


```html
{% raw %}
<ul>
    {% for key in keys %}
    {% getkey my_container key as value %}
    <li>{{ key }} = {{ value }}</li>
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
{% divide 10 2  as division_result %} <!-- Divide 10 by 2 -->

Division Result: {{ division_result }}

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
<img src='{% uploaded_image "subdir/my_image.png" width=480 rotate=45 %}'/>
{% endraw %}
```

!!! info "Missing Image"
    If the supplied image filename does not exist, it will be replaced with a placeholder image file

!!! warning "Invalid Image"
    If the supplied file is not a valid image, it will be replaced with a placeholder image file

#### Image Manipulation

The `{% raw %}{% uploaded_image %}{% endraw %}` tag supports some optional parameters for image manipulation. These can be used to adjust or resize the image - to reduce the size of the generated report file, for example.

```html
{% raw %}
{% load report %}
<img src='{% uploaded_image "image_file.png" width=500 rotate=45 %}'>
{% endraw %}```


### SVG Images

SVG images need to be handled in a slightly different manner. When embedding an uploaded SVG image, use the `{% raw %}{% encode_svg_image ... %}{% endraw %}` tag:

```html
{% raw %}
<!-- Load the report helper functions -->
{% load report %}
<img src='{% encode_svg_image svg_image_file %}'/>
{% endraw %}
```

### Part images

A shortcut function is provided for rendering an image associated with a Part instance. You can render the image of the part using the `{% raw %}{% part_image ... %}{% endraw %}` template tag:

```html
{% raw %}
<!-- Load the report helper functions -->
{% load report %}
<img src='{% part_image part %}'/>
{% endraw %}
```

#### Image Arguments

Any optional arguments which can be used in the [uploaded_image tag](#uploaded-images) can be used here too.

#### Image Variations

The *Part* model supports *preview* (256 x 256) and *thumbnail* (128 x 128) versions of the uploaded image. These variations can be used in the generated reports (e.g. to reduce generated file size):

```html
{% raw %}
{% load report %}
<!-- Render the "preview" image variation -->
<img src='{% part_image part preview=True %}'>

<!-- Render the "thumbnail" image variation -->
<img src='{% part_image part thumbnail=True %}'>
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

#### Image Variations

*Preview* and *thumbnail* image variations can be rendered for the `company_image` tag, in a similar manner to [part image variations](#image-variations)

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

## Part Parameters

If you need to load a part parameter for a particular Part, within the context of your template, you can use the `part_parameter` template tag.

The following example assumes that you have a report or label which contains a valid [Part](../part/part.md) instance:

```
{% raw %}
{% load report %}

{% part_parameter part "length" as length %}

Part: {{ part.name }}<br>
Length: {{ length.data }} [{{ length.units }}]

{% endraw %}
```

A [Part Parameter](../part/parameter.md) has the following available attributes:

| Attribute | Description |
| --- | --- |
| Name | The *name* of the parameter (e.g. "Length") |
| Description | The *description* of the parameter |
| Data | The *value* of the parameter (e.g. "123.4") |
| Units | The *units* of the parameter (e.g. "km") |
| Template | A reference to a [PartParameterTemplate](../part/parameter.md#parameter-templates) |
