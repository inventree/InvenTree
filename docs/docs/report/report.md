---
title: Report Generation
---

## Custom Reporting

InvenTree supports a customizable reporting ecosystem, allowing the user to develop reporting templates that meet their particular needs.

PDF reports are generated from custom HTML template files which are written by the user.

Reports are used in a variety of situations to format data in a friendly format for printing, distribution, conformance and testing.

In addition to providing the ability for end-users to provide their own reporting templates, some report types offer "built-in" report templates ready for use.

### WeasyPrint Templates

InvenTree report templates utilize the powerful [WeasyPrint](https://weasyprint.org/) PDF generation engine.

!!! info "WeasyPrint"
    WeasyPrint is an extremely powerful and flexible reporting library. Refer to the [WeasyPrint docs](https://doc.courtbouillon.org/weasyprint/stable/) for further information.

### Stylesheets

Templates are rendered using standard HTML / CSS - if you are familiar with web page layout, you're ready to go!

### Template Language

Uploaded report template files are passed through the [django template rendering framework]({% include "django.html" %}/topics/templates/), and as such accept the same variable template strings as any other django template file. Different variables are passed to the report template (based on the context of the report) and can be used to customize the contents of the generated PDF.

### Variables

Each report template is provided a set of *context variables* which can be used when rendering the template.

For example, rendering the name of a part (which is available in the particular template context as `part`) is as follows:

```html
{% raw %}

<!-- Template variables use {{ double_curly_braces }} -->
<h2>Part: {{ part.name }}</h3>
<p><i>
  Description:<br>
  {{ part.description }}
</p></i>
{% endraw %}
```

### Context Variables

!!! info "Context Variables"
  	Templates will have different variables available to them depending on the report type. Read the detailed information on each available report type for further information.

Please refer to the [Context variables](./context_variables.md) page.

### Conditional Rendering

The django template system allows for conditional rendering, providing conditional flow statements such as:

```
{% raw %}
{% if <condition> %}
{% do_something %}
{% elif <other_condition> %}
<!-- something else -->
{% else %}
<!-- finally -->
{% endif %}
{% endraw %}
```

```
{% raw %}
{% for <item> in <list> %}
Item: {{ item }}
{% endfor %}
{% endraw %}
```

!!! info "Conditionals"
    Refer to the [django template language documentation]({% include "django.html" %}/ref/templates/language/) for more information.

### Localization Issues

Depending on your localization scheme, inputting raw numbers into the formatting section template can cause some unintended issues. Consider the block below which specifies the page size for a rendered template:

```html
{% raw %}
<head>
    <style>
        @page {
            size: {{ width }}mm {{ height }}mm;
            margin: 0mm;
        }
    </style>
</head>
{% endraw %}
```

If localization settings on the InvenTree server use a comma (`,`) character as a decimal separator, this may produce an output like:

```html
{% raw %}
{% endraw %}
<head>
    <style>
        @page {
            size: 57,3mm 99,0mm;
            margin: 0mm;
        }
    </style>
</head>
```

The resulting `{% raw %}<style>{% endraw %}` CSS block will be *invalid*!

So, if you are writing a template which has custom formatting, (or any other sections which cannot handle comma decimal separators) you must wrap that section in a `{% raw %}{% localize off %}{% endraw %}` block:

```html
{% raw %}
<head>
    <style>
        @page {
            {% localize off %}
            size: {{ width }}mm {{ height }}mm;
            {% endlocalize %}
            margin: 0mm;
        }
    </style>
</head>
{% endraw %}
```

!!! tip "Close it out"
    Don't forget to end with a `{% raw %}{% endlocalize %}{% endraw %}` tag!

### Extending with Plugins

The [ReportMixin plugin class](../extend/plugins/report.md) allows reporting functionality to be extended with custom features.

## Report Types

InvenTree supports the following reporting functionality:

| Report Type | Description |
| --- | --- |
| [Test Report](./test.md) | Format results of a test report against for a particular StockItem |
| [Build Order Report](./build.md) | Format a build order report |
| [Purchase Order Report](./purchase_order.md) | Format a purchase order report |
| [Sales Order Report](./sales_order.md) | Format a sales order report |
| [Return Order Report](./return_order.md) | Format a return order report |
| [Stock Location Report](./stock_location.md) | Format a stock location report |

### Default Reports

InvenTree is supplied with a number of default templates "out of the box". These are generally quite simple, but serve as a starting point for building custom reports to suit a specific need.

!!! tip "Read the Source"
    The source code for the default reports is [available on GitHub](https://github.com/inventree/InvenTree/tree/master/InvenTree/report/templates/report). Use this as a guide for generating your own reports!

## Creating Reports

Report templates are created (and edited) via the [admin interface](../settings/admin.md), under the *Report* section. Select the certain type of report template you are wanting to create, and press the *Add* button in the top right corner:

{% with id="report-create", url="report/add_report_template.png", description="Create new report" %}
{% include 'img.html' %}
{% endwith %}

!!! tip "Staff Access Only"
    Only users with staff access can upload or edit report template files.

!!! info "Editing Reports"
    Existing reports can be edited from the admin interface, in the same location as described above. To change the contents of the template, re-upload a template file, to override the existing template data.

### Name and Description

Each report template requires a name and description, which identify and describe the report template.

### Enabled Status

Boolean field which determines if the specific report template is enabled, and available for use. Reports can be disabled to remove them from the list of available templates, but without deleting them from the database.

### Filename Pattern

The filename pattern used to generate the output `.pdf` file. Defaults to "report.pdf".

The filename pattern allows custom rendering with any context variables which are available to the report. For example, a [test report](./test.md) for a particular [Stock Item](../stock/stock.md#stock-item) can use the part name and serial number of the stock item when generating the report name:

{% with id="report-filename-pattern", url="report/filename_pattern.png", description="Report filename pattern" %}
{% include 'img.html' %}
{% endwith %}


### Report Filters

Each type of report provides a *filters* field, which can be used to filter which items a report can be generated against. The target of the *filters* field depends on the type of report - refer to the documentation on the specific report type for more information.

For example, the [Test Report](./test.md) filter targets the linked [Stock Item](../stock/status.md) object, and can be used to select which stock items are allowed for the given report. Let's say that a certain test report should only be generated for "trackable" stock items. A filter could easily be constructed to accommodate this, by limiting available items to those where the associated [Part](../part/part.md) is *trackable*:

{% with id="report-filter-valid", url="report/filters_valid.png", description="Report filter  selection" %}
{% include 'img.html' %}
{% endwith %}

If you enter an invalid option for the filter field, an error message will be displayed:

{% with id="report-filter-invalid", url="report/filters_invalid.png", description="Invalid filter selection" %}
{% include 'img.html' %}
{% endwith %}

!!! warning "Advanced Users"
    Report filtering is an advanced topic, and requires a little bit of knowledge of the underlying data structure!

### Metadata

A JSON field made available to any [plugins](../extend/plugins.md) - but not used by internal code.

## Report Options

A number of global reporting options are available for customizing InvenTree reports:

{% with id="report-options", url="report/report.png", description="Report Options" %}
{% include 'img.html' %}
{% endwith %}

### Enable Reports

By default, the reporting feature is disabled. It must be enabled in the global settings.


### Default Page Size

The built-in InvenTree report templates (and any reports which are derived from the built-in templates) use the *Page Size* option to set the page size of the generated reports.

!!! info "Override Page Size"
    Custom report templates do not have to make use of the *Page Size* option, although it is made available to the template context.

### Debug Mode

As templates are rendered directly to a PDF object, it can be difficult to debug problems when the PDF does not render exactly as expected.

Setting the *Debug Mode* option renders the template as raw HTML instead of PDF, allowing the rendering output to be introspected. This feature allows template designers to understand any issues with the generated HTML (before it is passed to the PDF generation engine).

!!! warning "HTML Rendering Limitations"
    When rendered in debug mode, @page attributes (such as size, etc) will **not** be observed. Additionally, any asset files stored on the InvenTree server will not be rendered. Debug mode is not intended to produce "good looking" documents!

## Report Assets

User can upload asset files (e.g. images) which can be used when generating reports. For example, you may wish to generate a report with your company logo in the header. Asset files are uploaded via the admin interface.

Asset files can be rendered directly into the template as follows

```html
{% raw %}
<!-- Need to include the report template tags at the start of the template file -->
{% load report %}

<!-- Simple stylesheet -->
<head>
  <style>
    .company-logo {
      height: 50px;
    }
  </style>
</head>

<body>
<!-- Report template code here -->

<!-- Render an uploaded asset image -->
<img src="{% asset 'company_image.png' %}" class="company-logo">

<!-- ... -->
</body>

{% endraw %}
```

!!! warning "Asset Naming"
    If the requested asset name does not match the name of an uploaded asset, the template will continue without loading the image.

!!! info "Assets location"
    You need to ensure your asset images to the report/assets directory in the [data directory](../start/docker_dev.md/#data-directory). Upload new assets via the [admin interface](../settings/admin.md) to ensure they are uploaded to the correct location on the server.


## Report Snippets

A powerful feature provided by the django / WeasyPrint templating framework is the ability to include external template files. This allows commonly used template features to be broken out into separate files and re-used across multiple templates.

To support this, InvenTree provides report "snippets" - short (or not so short) template files which cannot be rendered by themselves, but can be called from other templates.

Similar to assets files, snippet template files are uploaded via the admin interface.

Snippets are included in a template as follows:

```
{% raw %}{% include 'snippets/<snippet_name.html>' %}{% endraw %}
```

For example, consider a stocktake report for a particular stock location, where we wish to render a table with a row for each item in that location.

```html
{% raw %}

<table class='stock-table'>
  <thead>
    <!-- table header data -->
  </thead>
  <tbody>
    {% for item in location.stock_items %}
    {% include 'snippets/stock_row.html' with item=item %}
    {% endfor %}
  </tbody>

{% endraw %}
```

!!! info "Snippet Arguments"
    Note above that named argument variables can be passed through to the snippet!

And the snippet file `stock_row.html` may be written as follows:

```html
{% raw %}
<!-- stock_row snippet -->
<tr>
  <td>{{ item.part.full_name }}</td>
  <td>{{ item.quantity }}</td>
</tr>
{% endraw %}
```
