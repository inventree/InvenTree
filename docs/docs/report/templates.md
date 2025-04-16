---
title: InvenTree Templates
---

## Template Overview

InvenTree supports a customizable reporting ecosystem, allowing the user to develop document templates that meet their particular needs.

PDF files are generated from custom HTML template files which are written by the user.

Templates can be used to generate *reports* or *labels* which can be  used in a variety of situations to format data in a friendly format for printing, distribution, conformance and testing.

In addition to providing the ability for end-users to provide their own reporting templates, some report types offer "built-in" report templates ready for use.

## Template Types

The following types of templates are available:

### Reports

Reports are intended to serve as formal documents, and can be used to generate formatted PDF outputs for a variety of purposes.

Refer to the [report templates](./report.md) documentation for further information.

### Labels

Labels can also be generated using the templating system. Labels are intended to be used for printing small, formatted labels for items, parts, locations, etc.

Refer to the [label templates](./labels.md) documentation for further information.

### Template Model Types

When generating a particular template (to render a report or label output), the template is rendered against a particular "model" type. The model type determines the data that is available to the template, and how it is formatted.

To read more about the model types for which templates can be rendered, and the associated context information, refer to the [context variables](./context_variables.md) documentation.

### Default Reports

InvenTree is supplied with a number of default templates "out of the box" - for generating both labels and reports. These are generally quite simple, but serve as a starting point for building custom reports to suit a specific need.

!!! tip "Read the Source"
    The source code for the default reports is [available on GitHub]({{ sourcedir("src/backend/InvenTree/report/templates/report") }}). Use this as a guide for generating your own reports!

### Extending with Plugins

The [ReportMixin plugin class](../extend/plugins/report.md) allows reporting functionality to be extended with custom features.

## WeasyPrint Template Rendering

InvenTree report templates utilize the powerful [WeasyPrint](https://weasyprint.org/) PDF generation engine.

To read more about the capabilities of the report templating engine, and how to use it, refer to the [weasyprint documentation](./weasyprint.md).

## Creating Templates

Report and label templates can be created (and edited) via the [admin interface](../settings/admin.md), under the *Report* section.

Select the type of template you are wanting to create (a *Report Template* or *Label Template*) and press the *Add* button in the top right corner:

{% with id="report-list", url="report/report_template_admin.png", description="Report templates in admin interface" %}
{% include 'img.html' %}
{% endwith %}

!!! tip "Staff Access Only"
    Only users with staff access can upload or edit report template files.

!!! info "Editing Reports"
    Existing reports can be edited from the admin interface, in the same location as described above. To change the contents of the template, re-upload a template file, to override the existing template data.

!!! tip "Template Editor"
    InvenTree also provides a powerful [template editor](./template_editor.md) which allows for the creation and editing of report templates directly within the browser.

### Name and Description

Each report template requires a name and description, which identify and describe the report template.

### Enabled Status

Boolean field which determines if the specific report template is enabled, and available for use. Reports can be disabled to remove them from the list of available templates, but without deleting them from the database.

### Filename Pattern

The filename pattern used to generate the output `.pdf` file. Defaults to "report.pdf".

The filename pattern allows custom rendering with any context variables which are available to the report. For example, a test report for a particular [Stock Item](../stock/stock.md#stock-item) can use the part name and serial number of the stock item when generating the report name:

{% with id="report-filename-pattern", url="report/filename_pattern.png", description="Report filename pattern" %}
{% include 'img.html' %}
{% endwith %}


### Template Filters

Each template instance provides a *filters* field, which can be used to filter which items a report or label template can be generated against. The target of the *filters* field depends on the model type associated with the particular template.

As an example, let's say that a certain `StockItem` report should only be generated for "trackable" stock items. A filter could easily be constructed to accommodate this, by limiting available items to those where the associated [Part](../part/part.md) is *trackable*:

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

## Reporting Options

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
    Upload new assets via the [admin interface](../settings/admin.md) to ensure they are uploaded to the correct location on the server.


## Report Snippets

A powerful feature provided by the django / WeasyPrint templating framework is the ability to include external template files. This allows commonly used template features to be broken out into separate files and reused across multiple templates.

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
