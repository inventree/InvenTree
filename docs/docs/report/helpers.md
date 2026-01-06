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
    To see the full range of available helper functions, refer to the source file [report.py]({{ sourcefile("src/backend/InvenTree/report/templatetags/report.py") }}) where these functions are defined!

## Assigning Variables

When making use of helper functions within a template, it can be useful to store the result of the function to a variable, rather than immediately rendering the output.

For example, using the [render_currency](#currency-formatting) helper function, we can store the output to a variable which can be used at a later point in the template:

```html
{% raw %}

{% load report %}

{% render_currency 12.3 currency='USD' as myvar %}
...
...
Result: {{ myvar }}

{% endraw %}
```

Note the use of the `as` keyword to assign the output of the function to a variable. This can be used to assign the result of a function to a named variable, which can then be used later in the template.

## Data Structure Access

A number of helper functions are available for accessing data contained in a particular structure format:

### Index Access

To return the element at a given index in a container which supports indexed access (such as a [list](https://www.w3schools.com/python/python_lists.asp)), use the `getindex` function:

::: report.templatetags.report.getindex
    options:
        show_docstring_description: false
        show_source: False

#### Example

```html
{% raw %}
{% getindex my_list 1 as value %}
Item: {{ value }}
{% endraw %}
```

### Key Access

To return an element corresponding to a certain key in a container which supports key access (such as a [dictionary](https://www.w3schools.com/python/python_dictionaries.asp)), use the `getkey` function:


::: report.templatetags.report.getkey
    options:
        show_docstring_description: false
        show_source: False

#### Example

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

## Database Helpers

A number of helper functions are available for accessing database objects:

### order_queryset

The `order_queryset` function allows for ordering of a provided queryset. It takes a queryset and a list of ordering arguments, and returns an ordered queryset.

::: report.templatetags.report.order_queryset
    options:
        show_docstring_description: false
        show_source: False

!!! info "Provided QuerySet"
    The provided queryset must be a valid Django queryset object, which is already available in the template context.

#### Example

In a report template which has a `PurchaseOrder` object available in its context as the variable `order`, return the matching line items ordered by part name:

```html
{% raw %}
{% load report %}

{% order_queryset order.lines.all 'part__name' as ordered_lines %}
```

### filter_queryset

The `filter_queryset` function allows for arbitrary filtering of the provided queryset. It takes a queryset and a list of filter arguments, and returns a filtered queryset.

::: report.templatetags.report.filter_queryset
    options:
        show_docstring_description: false
        show_source: False

!!! info "Provided QuerySet"
    The provided queryset must be a valid Django queryset object, which is already available in the template context.

!!! warning "Advanced Users"
    The `filter_queryset` function is a powerful tool, but it is also easy to misuse. It assumes that the user has a good understanding of Django querysets and the underlying database structure.

#### Example

In a report template which has a `PurchaseOrder` object available in its context, fetch any line items which have a received quantity greater than zero:

```html
{% raw %}
{% load report %}

{% filter_queryset order.lines.all received__gt=0 as received_lines %}

<ul>
  {% for line in received_lines %}
  <li>{{ line.part.part.full_name }} - {{ line.received }} / {{ line.quantity }}</li>
    {% endfor %}
</ul>

{% endraw %}
```

### filter_db_model

The `filter_db_model` function allows for filtering of a database model based on a set of filter arguments. It takes a model class and a list of filter arguments, and returns a filtered queryset.

::: report.templatetags.report.filter_db_model
    options:
        show_docstring_description: false
        show_source: False

#### Example

Generate a list of all active customers:

```html
{% raw %}
{% load report %}

{% filter_db_model 'company.company' is_customer=True active=True as active_customers %}

<ul>
    {% for customer in active_customers %}
    <li>{{ customer.name }}</li>
    {% endfor %}
</ul>

{% endraw %}
```

### Advanced Database Queries

More advanced database filtering should be achieved using a [report plugin](../plugins/mixins/report.md), and adding custom context data to the report template.

## Number Formatting

### format_number

The helper function `format_number` allows for some common number formatting options. It takes a number (or a number-like string) as an input, as well as some formatting arguments. It returns a *string* containing the formatted number:

::: report.templatetags.report.format_number
    options:
        show_docstring_description: false
        show_source: False

#### Example

```html
{% raw %}
{% load report %}
{% format_number 3.14159265359 decimal_places=5, leading=3 %}
<!-- output: 0003.14159 -->
{% format_number 3.14159265359 integer=True %}
<!-- output: 3 -->
{% endraw %}
```

## Date Formatting

For rendering date and datetime information, the following helper functions are available:

### format_date

::: report.templatetags.report.format_date
    options:
        show_docstring_description: false
        show_source: False

### format_datetime

::: report.templatetags.report.format_datetime
    options:
        show_docstring_description: false
        show_source: False

### Date Formatting

If not specified, these methods return a result which uses ISO formatting. Refer to the [datetime format codes](https://docs.python.org/3/library/datetime.html#format-codes) for more information! |


### Example

A simple example of using the date formatting helper functions:

```html
{% raw %}
{% load report %}
Date: {% format_date my_date timezone="Australia/Sydney" %}
Datetime: {% format_datetime my_datetime format="%d-%m-%Y %H:%M%S" %}
{% endraw %}
```

## Currency Formatting

### render_currency

The helper function `render_currency` allows for simple rendering of currency data. This function can also convert the specified amount of currency into a different target currency:

::: InvenTree.helpers_model.render_currency
    options:
        show_docstring_description: false
        show_source: False


#### Example

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

### convert_currency

To convert a currency value from one currency to another, use the `convert_currency` helper function:

::: report.templatetags.report.convert_currency
    options:
        show_docstring_description: false
        show_source: False

!!! info "Data Types"
    The `money` parameter must be `Money` class instance. If not, an error will be raised.

### create_currency

Create a `currency` instance using the `create_currency` helper function. This returns a `Money` class instance based on the provided amount and currency type.

::: report.templatetags.report.create_currency
    options:
        show_docstring_description: false
        show_source: False

## Maths Operations

Simple mathematical operators are available, as demonstrated in the example template below. These operators can be used to perform basic arithmetic operations within the report template.

!!! info "Input Types"
    These mathematical functions accept inputs of various input types, and attempt to perform the operation accordingly. Note that any inputs which are provided as strings or numbers will be converted to `Decimal` class types before the operation is performed.

### add

Add two numbers together using the `add` helper function:

::: report.templatetags.report.add
    options:
        show_docstring_description: false
        show_source: False

### subtract

Subtract one number from another using the `subtract` helper function:

::: report.templatetags.report.subtract
    options:
        show_docstring_description: false
        show_source: False

### multiply

Multiply two numbers together using the `multiply` helper function:

::: report.templatetags.report.multiply
    options:
        show_docstring_description: false
        show_source: False

### divide

Divide one number by another using the `divide` helper function:

::: report.templatetags.report.divide
    options:
        show_docstring_description: false
        show_source: False

### modulo

Perform a modulo operation using the `modulo` helper function:

::: report.templatetags.report.modulo
    options:
        show_docstring_description: false
        show_source: False

### Example

```html
{% raw %}
<!-- Load the report helper functions -->
{% load report %}

{% add 1 3 %} <!-- Add two numbers together -->
{% subtract 4 3 %} <!-- Subtract 3 from 4 -->
{% multiply 1.2 3.4 %} <!-- Multiply two numbers -->

<!-- Perform a calculation and store the result -->
{% divide 10 2 as division_result %} <!-- Divide 10 by 2 -->

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

### uploaded_image

You can access an uploaded image file if you know the *path* of the image, relative to the top-level `/media/` directory. To load the image into a report, use the `{% raw %}{% uploaded_image ... %}{% endraw %}` tag:

::: report.templatetags.report.uploaded_image
    options:
        show_docstring_description: false
        show_source: False

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


### encode_svg_image

::: report.templatetags.report.encode_svg_image
    options:
        show_docstring_description: false
        show_source: False

SVG images need to be handled in a slightly different manner. When embedding an uploaded SVG image, use the `{% raw %}{% encode_svg_image ... %}{% endraw %}` tag:

```html
{% raw %}
<!-- Load the report helper functions -->
{% load report %}
<img src='{% encode_svg_image svg_image_file %}'/>
{% endraw %}
```

### part_image

A shortcut function is provided for rendering an image associated with a Part instance. You can render the image of the part using the `{% raw %}{% part_image ... %}{% endraw %}` template tag:

::: report.templatetags.report.part_image
    options:
        show_docstring_description: false
        show_source: False

```html
{% raw %}
<!-- Load the report helper functions -->
{% load report %}
<img src='{% part_image part %}'/>
{% endraw %}
```

#### Image Arguments

Any optional arguments which can be used in the [uploaded_image tag](#uploaded_image) can be used here too.

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


### company_image

A shortcut function is provided for rendering an image associated with a Company instance. You can render the image of the company using the `{% raw %}{% company_image ... %}{% endraw %}` template tag:

::: report.templatetags.report.company_image
    options:
        show_docstring_description: false
        show_source: False

```html
{% raw %}
<!-- Load the report helper functions -->
{% load report %}
<img src='{% company_image company %}'/>
{% endraw %}
```

#### Image Variations

*Preview* and *thumbnail* image variations can be rendered for the `company_image` tag, in a similar manner to [part image variations](#image-variations)

## Icons

Some models (e.g. part categories and locations) allow to specify a custom icon. To render these icons in a report, there is a `{% raw %}{% icon location.icon %}{% endraw %}` template tag from the report template library available.

This tag renders the required html for the icon.

!!! info "Loading fonts"
    Additionally the icon fonts need to be loaded into the template. This can be done using the `{% raw %}{% include_icon_fonts %}{% endraw %}` template tag inside of a style block

!!! tip "Custom classes for styling the icon further"
    The icon template tag accepts an optional `class` argument which can be used to apply a custom class to the rendered icon used to style the icon further e.g. positioning it, changing it's size, ... `{% raw %}{% icon location.icon class="my-class" %}{% endraw %}`.

```html
{% raw %}
{% load report %}

{% block style %}
{% include_icon_fonts %}
{% endblock style %}

{% icon location.icon %}

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

If the system administrator has enabled a [custom logo](../start/config.md#customization-options) then this logo will be used instead of the base InvenTree logo.

This is a useful way to get a custom company logo into your reports.

If you have a custom logo, but explicitly wish to load the InvenTree logo itself, add `custom=False` to the tag:

```html
{% raw %}
{% load report %}
<img src='{% logo_image custom=False %}'/>
{% endraw %}
```

## Report Assets

[Report Assets](./index.md#report-assets) are files specifically uploaded by the user for inclusion in generated reports and labels.

You can add asset images to the reports and labels by using the `{% raw %}{% asset ... %}{% endraw %}` template tag:

```html
{% raw %}
<!-- Load the report helper functions -->
{% load report %}
<img src="{% asset 'my_awesome_logo.png' %}"/>
{% endraw %}
```

## Parameters

If you need to load a parameter value for a particular model instance, within the context of your template, you can use the `parameter` template tag:

::: report.templatetags.report.parameter
    options:
        show_docstring_description: false
        show_source: False

### Example

The following example assumes that you have a report or label which contains a valid [Part](../part/index.md) instance:

```
{% raw %}
{% load report %}

{% parameter part "length" as length %}

Part: {{ part.name }}<br>
Length: {{ length.data }} [{{ length.units }}]

{% endraw %}
```

A [Parameter](../concepts/parameters.md) has the following available attributes:

| Attribute | Description |
| --- | --- |
| Name | The *name* of the parameter (e.g. "Length") |
| Description | The *description* of the parameter |
| Data | The *value* of the parameter (e.g. "123.4") |
| Units | The *units* of the parameter (e.g. "km") |
| Template | A reference to a [ParameterTemplate](../concepts/parameters.md#parameter-templates) |

## Rendering Markdown

Some data fields (such as the *Notes* field available on many internal database models) support [markdown formatting](https://en.wikipedia.org/wiki/Markdown). To render markdown content in a custom report, there are template filters made available through the [django-markdownify](https://github.com/erwinmatijsen/django-markdownify) library. This library provides functionality for converting markdown content to HTML representation, allowing it to be then rendered to PDF by the InvenTree report generation pipeline.

To render markdown content in a report, consider the following simplified example:

```html
{% raw %}

{% load markdownify %}

<h3>Part Notes</h3>
<p>
    {{ part.notes | markdownify }}
</p>
{% endraw %}
```

You can read further details in the [django-markdownify documentation](https://django-markdownify.readthedocs.io/en/latest/).

## List of tags and filters

The following tags and filters are available.

{{ tags_and_filters() }}
