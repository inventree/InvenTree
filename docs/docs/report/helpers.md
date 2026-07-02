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

## List Helpers

The following helper functions are available for working with list (or list-like) data structures:

### length

Return the length of a list (or list-like) data structure. Note that this will also work for other data structures which support the `len()` function, such as strings, dictionaries or querysets:

::: report.templatetags.report.length
    options:
        show_docstring_description: false
        show_source: False

### first

Return the first element of a list (or list-like) data structure:

::: report.templatetags.report.first
    options:
        show_docstring_description: false
        show_source: False


### last

Return the last element of a list (or list-like) data structure:

::: report.templatetags.report.last
    options:
        show_docstring_description: false
        show_source: False

### reverse

Return a list (or list-like) data structure in reverse order:

::: report.templatetags.report.reverse
    options:
        show_docstring_description: false
        show_source: False

### truncate

Return a truncated version of a list (or list-like) data structure, containing only the first N elements:

::: report.templatetags.report.truncate
    options:
        show_docstring_description: false
        show_source: False

## String Formatting

### strip

Return a string with leading and trailing whitespace removed:

::: report.templatetags.report.strip
    options:
        show_docstring_description: false
        show_source: False


### lstrip

Return a string with leading whitespace removed:

::: report.templatetags.report.lstrip
    options:
        show_docstring_description: false
        show_source: False

### rstrip

Return a string with trailing whitespace removed:

::: report.templatetags.report.rstrip
    options:
        show_docstring_description: false
        show_source: False

### split

Return a list of substrings by splitting a string based on a specified separator:

::: report.templatetags.report.split
    options:
        show_docstring_description: false
        show_source: False

### join

Return a string by joining a list of strings into a single string, using a specified separator:

::: report.templatetags.report.join
    options:
        show_docstring_description: false
        show_source: False

### replace

Return a string where occurrences of a specified substring are replaced with another substring:

::: report.templatetags.report.replace
    options:
        show_docstring_description: false
        show_source: False

### lowercase

Return a string with all characters converted to lowercase:

::: report.templatetags.report.lowercase
    options:
        show_docstring_description: false
        show_source: False

### uppercase

Return a string with all characters converted to uppercase:

::: report.templatetags.report.uppercase
    options:
        show_docstring_description: false
        show_source: False

### titlecase

Return a string with the first character of each word converted to uppercase and the remaining characters converted to lowercase:

::: report.templatetags.report.titlecase
    options:
        show_docstring_description: false
        show_source: False

## Number Formatting

A number of helper functions are available for formatting numbers in a particular way. These can be used to format numbers according to a particular number of decimal places, or to add leading zeros, for example.

### format_number

The helper function `format_number` allows for some common number formatting options. It takes a number (or a number-like string) as an input, as well as some formatting arguments. It returns a *string* containing the formatted number:

::: report.templatetags.report.format_number
    options:
        show_docstring_description: false
        show_source: False

#### Examples

```html
{% raw %}
{% load report %}

<!-- Basic usage: strip trailing zeros -->
{% format_number 3.14159265359 decimal_places=5 %}
<!-- output: 3.14159 -->

<!-- Leading zeros with 'leading' option -->
{% format_number 3.14159265359 decimal_places=5 leading=3 %}
<!-- output: 003.14159 -->

<!-- Round to integer -->
{% format_number 3.14159265359 integer=True %}
<!-- output: 3 -->

<!-- Thousands separator -->
{% format_number 9988776.5 decimal_places=2 separator=True %}
<!-- output: 9,988,776.50 -->

<!-- Locale-aware formatting: decimal comma, dot thousands separator -->
{% format_number 9988776.5 decimal_places=2 separator=True locale='de-de' %}
<!-- output: 9.988.776,50 -->

<!-- Scale a value with a multiplier before formatting -->
{% format_number 0.175 multiplier=100 decimal_places=1 %}
<!-- output: 17.5 -->

<!-- Allow up to N significant decimal places, but suppress trailing zeros -->
{% format_number 1234.5 decimal_places=2 max_decimal_places=6 %}
<!-- output: 1234.5 -->

{% endraw %}
```

#### Custom Format Strings

The `fmt` argument accepts a [Unicode number pattern](https://unicode.org/reports/tr35/tr35-numbers.html#Number_Format_Patterns) string (the same syntax used by [Babel](https://babel.pocoo.org/en/latest/numbers.html)). When `fmt` is provided it takes complete priority over the `decimal_places`, `max_decimal_places`, `leading`, and `separator` arguments — those arguments are silently ignored.

The `integer` and `multiplier` arguments **are** still applied to the number before the format string is used.

| Symbol | Meaning |
| --- | --- |
| `0` | Required digit — always rendered, even if zero |
| `#` | Optional digit — suppressed when not significant |
| `,` | Grouping separator (position defines group size) |
| `.` | Decimal separator |

Common patterns:

| Pattern | Example output |
| --- | --- |
| `0` | `1235` |
| `#,##0` | `1,235` |
| `0.00` | `1234.57` |
| `#,##0.00` | `1,234.57` |
| `000` | `007` |

```html
{% raw %}
{% load report %}

<!-- Two decimal places, no grouping -->
{% format_number 1234.5678 fmt='0.00' %}
<!-- output: 1234.57 -->

<!-- Two decimal places with thousands separator -->
{% format_number 1234.5678 fmt='#,##0.00' %}
<!-- output: 1,234.57 -->

<!-- Same pattern, German locale: dot thousands, comma decimal -->
{% format_number 1234.5678 fmt='#,##0.00' locale='de-de' %}
<!-- output: 1.234,57 -->

<!-- Integer with thousands separator, large number -->
{% format_number 9988776655.4321 fmt='#,##0' integer=True %}
<!-- output: 9,988,776,655 -->

{% endraw %}
```

## Date Formatting

For rendering date and datetime information, the following helper functions are available:

Both functions resolve their output using the following priority order:

1. **`fmt=` argument** — a [strftime format string](https://docs.python.org/3/library/datetime.html#format-codes). When provided, this takes full priority; `locale` and `date_format` are ignored.
2. **`locale=` argument** — when no `fmt` is given, Babel formats the value using the style set by `date_format` (default `medium`).
3. **Server `LANGUAGE_CODE`** — used as the locale when no `locale=` argument is supplied.

#### Date Format Styles

The `date_format` argument controls how Babel renders the date when locale-aware formatting is used. The four named styles are:

| Style | `format_date` example (en-us, 2025-01-12) | `format_datetime` example (en-us, 2025-01-12 14:30) |
| --- | --- | --- |
| `full` | `Sunday, January 12, 2025` | `Sunday, January 12, 2025 at 2:30:00 PM UTC` |
| `long` | `January 12, 2025` | `January 12, 2025 at 2:30:00 PM UTC` |
| `medium` *(default)* | `Jan 12, 2025` | `Jan 12, 2025, 2:30:00 PM` |
| `short` | `1/12/25` | `1/12/25, 2:30 PM` |

The exact output varies by locale — the table above uses `en-us`.

### format_date

::: report.templatetags.report.format_date
    options:
        show_docstring_description: false
        show_source: False

#### Examples

```html
{% raw %}
{% load report %}

<!-- Default: medium style, locale from LANGUAGE_CODE -->
{% format_date my_date %}
<!-- output (en-us): Jan 12, 2025 -->

<!-- Explicit strftime format string — locale and date_format are ignored -->
{% format_date my_date fmt="%d/%m/%Y" %}
<!-- output: 12/01/2025 -->

<!-- Locale-aware, default medium style -->
{% format_date my_date locale='en-us' %}
<!-- output: Jan 12, 2025 -->

<!-- Short style -->
{% format_date my_date locale='en-us' date_format='short' %}
<!-- output: 1/12/25 -->

<!-- Full style -->
{% format_date my_date locale='en-us' date_format='full' %}
<!-- output: Sunday, January 12, 2025 -->

{% endraw %}
```

### format_datetime

::: report.templatetags.report.format_datetime
    options:
        show_docstring_description: false
        show_source: False

#### Examples

```html
{% raw %}
{% load report %}

<!-- Default: medium style, locale from LANGUAGE_CODE -->
{% format_datetime my_datetime %}
<!-- output (en-us): Jan 12, 2025, 2:30:00 PM -->

<!-- Explicit strftime format — locale and date_format are ignored -->
{% format_datetime my_datetime fmt="%d-%m-%Y %H:%M" %}
<!-- output: 12-01-2025 14:30 -->

<!-- Locale-aware, default medium style -->
{% format_datetime my_datetime locale='en-us' %}
<!-- output: Jan 12, 2025, 2:30:00 PM -->

<!-- Short style -->
{% format_datetime my_datetime locale='de-de' date_format='short' %}
<!-- output: 12.01.25, 14:30 -->

<!-- Convert to a specific timezone before formatting -->
{% format_datetime my_datetime timezone="Australia/Sydney" locale='en-au' %}

{% endraw %}
```

## Currency Formatting

### render_currency

The helper function `render_currency` allows for simple rendering of currency data. This function can also convert the specified amount of currency into a different target currency:

::: report.templatetags.report.render_currency
    options:
        show_docstring_description: false
        show_source: False

#### Decimal Places

When no decimal place arguments are provided, the locale/currency standard is used (e.g. 2 places for USD, 0 for JPY).

`decimal_places` and `max_decimal_places` work the same way as in [`format_number`](#format_number):

| Argument | Effect |
| --- | --- |
| `decimal_places=N` | Forces exactly N decimal digits (zero-padded) |
| `max_decimal_places=M` | Allows up to M decimal digits, suppressing trailing zeros beyond `decimal_places` |
| Both set | Forced minimum of `decimal_places`, optional up to `max_decimal_places` |
| Neither set | Locale/currency default (e.g. 2 for USD) |

```html
{% raw %}
{% load report %}

<!-- locale default for USD: 2 decimal places -->
{% render_currency order.total_price currency='USD' %}
<!-- output: $1,234.56 -->

<!-- force 3 decimal places -->
{% render_currency order.total_price currency='USD' decimal_places=3 %}
<!-- output: $1,234.560 -->

<!-- at least 2, up to 4 — trailing zeros beyond the value are suppressed -->
{% render_currency order.total_price currency='USD' decimal_places=2 max_decimal_places=4 %}
<!-- output: $1,234.5600 or $1,234.56 depending on the value -->

{% endraw %}
```

#### Locale and Symbol Rendering

The locale controls how the currency symbol and separators are rendered. For example, `USD 1234.56` with various locales:

| Locale | Output |
| --- | --- |
| `en-us` | `$1,234.56` |
| `en-gb` | `US$1,234.56` |
| `en-au` | `USD1,234.56` |
| `de-de` | `1.234,56 $` |

The locale is resolved in the following priority order:

1. **Explicit `locale=` argument** — highest priority, always wins
2. **Server `LANGUAGE_CODE`** — fallback

#### Leading Digits

The `leading` argument specifies the minimum number of digits to render before the decimal point (zero-padded). This works identically to `leading` in [`format_number`](#format_number):

```html
{% raw %}
{% load report %}

<!-- default: no padding -->
{% render_currency order.total_price currency='USD' %}
<!-- output: $1.23 -->

<!-- force at least 4 integer digits -->
{% render_currency order.total_price currency='USD' leading=4 %}
<!-- output: $0,001.23 -->

{% endraw %}
```

#### Custom Format Strings

The `fmt` argument accepts a [Unicode number pattern](https://unicode.org/reports/tr35/tr35-numbers.html#Number_Format_Patterns) string (same syntax as [`format_number`](#custom-format-strings)). **When `fmt` is provided, it takes complete priority over `decimal_places`, `max_decimal_places`, and `leading`** — those arguments are ignored.

The `locale`, `currency`, `multiplier`, and `include_symbol` arguments are still applied when `fmt` is set.

To include the currency symbol in a `fmt` pattern, use the `¤` placeholder. Without it, no symbol appears regardless of `include_symbol`.

| Pattern | Example output (en-us, USD) |
| --- | --- |
| `#,##0.00` | `1,234.56` (no symbol) |
| `¤#,##0.00` | `$1,234.56` |
| `¤#,##0.0000` | `$1,234.5600` |
| `¤ #,##0.00` | `$ 1,234.56` |

```html
{% raw %}
{% load report %}

<!-- No symbol (no ¤ in pattern) -->
{% render_currency order.total_price currency='USD' fmt='#,##0.00' %}
<!-- output: 1,234.56 -->

<!-- Symbol via ¤ placeholder -->
{% render_currency order.total_price currency='USD' fmt='¤#,##0.0000' locale='en-us' %}
<!-- output: $1,234.5600 -->

<!-- fmt + locale: de-de separators -->
{% render_currency order.total_price currency='USD' fmt='#,##0.00' locale='de-de' %}
<!-- output: 1.234,56 -->

<!-- fmt takes priority — decimal_places=2 is ignored -->
{% render_currency order.total_price currency='USD' fmt='0.0000' decimal_places=2 %}
<!-- output: 1234.5600 -->

{% endraw %}
```

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

<!-- Force 2 decimal places, convert to NZD -->
Total Price: {% render_currency order.total_price currency='NZD' decimal_places=2 %}

<!-- US-style symbol, regardless of server locale -->
Total Price: {% render_currency order.total_price currency='USD' locale='en-us' %}

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

If you need to reference a parameter for a particular model instance, within the context of your template, you can use the `parameter` template tag:

### parameter

This returns a [Parameter](../concepts/parameters.md) object which contains the value of the parameter, as well as any associated metadata (e.g. units, description, etc).

::: report.templatetags.report.parameter
    options:
        show_docstring_description: false
        show_source: False

#### Example

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

### parameter_value

To access just the value of a parameter, use the `parameter_value` template tag:

::: report.templatetags.report.parameter_value
    options:
        show_docstring_description: false
        show_source: False

#### Example

```
{% raw %}
{% load report %}

{% parameter_value part "length" backup_value="3"as length_value %}
Part: {{ part.name }}<br>
Length: {{ length_value }}
{% endraw %}
```

## Notes

[Notes](../concepts/notes.md) are rich-text documents that can be attached to most InvenTree model instances. Two template tags are available for accessing note content in a report.

### note

The `note` tag returns the rendered HTML content of a note, ready to embed directly in a report. Any images embedded in the note are automatically resolved to their base64-encoded data so that they appear in the generated PDF.

::: report.templatetags.report.note
    options:
        show_docstring_description: false
        show_source: False

If no `title` argument is given, the [primary note](../concepts/notes.md#primary-note) is returned. If a `title` is given, the note whose title matches (case-insensitively) is returned instead. An empty string is returned when no matching note exists.

#### Example

```html
{% raw %}
{% load report %}

<!-- Render the primary note for the part -->
{% note part as part_note %}
<div>{{ part_note }}</div>

<!-- Render a note by title -->
{% note part "Assembly Instructions" as instructions %}
<div>{{ instructions }}</div>
{% endraw %}
```

!!! info "Safe HTML Output"
    The `note` tag returns pre-sanitized HTML and is marked safe for direct template rendering. Do **not** additionally wrap it with `| safe` or `| markdownify` — the content has already been processed.

### note_instance

The `note_instance` tag returns the `Note` object itself, giving access to its individual fields. This is useful when you need to display the note title, description, or metadata alongside its content.

::: report.templatetags.report.note_instance
    options:
        show_docstring_description: false
        show_source: False

A `Note` object exposes the following attributes:

| Attribute | Description |
| --- | --- |
| `title` | The title of the note |
| `description` | An optional short description of the note |
| `content` | The raw HTML content of the note |
| `primary` | `True` if this is the primary note for the model instance |
| `updated` | Timestamp of the last modification |
| `updated_by` | The user who last modified the note |

#### Example

```html
{% raw %}
{% load report %}

{% note_instance part as primary_note %}
{% if primary_note %}
<h3>{{ primary_note.title }}</h3>
{% if primary_note.description %}<p><em>{{ primary_note.description }}</em></p>{% endif %}
{% note part as note_content %}
<div>{{ note_content }}</div>
{% endif %}
{% endraw %}
```

### Iterating Over All Notes

When a model has multiple notes and you want to render all of them, access the `notes` queryset directly:

```html
{% raw %}
{% load report %}

{% for n in part.notes.all %}
<h3>{{ n.title }}</h3>
{% note part n.title as note_content %}
<div>{{ note_content }}</div>
{% endfor %}
{% endraw %}
```

!!! tip "Ordering Notes"
    Use the [`order_queryset`](#order_queryset) helper to control the order in which notes are rendered, for example `{% order_queryset part.notes.all 'title' as ordered_notes %}`.

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
