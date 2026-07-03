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

The [ReportMixin plugin class](../plugins/mixins/report.md) allows reporting functionality to be extended with custom features.

## WeasyPrint Template Rendering

InvenTree report templates utilize the powerful [WeasyPrint](https://weasyprint.org/) PDF generation engine.

To read more about the capabilities of the report templating engine, and how to use it, refer to the [weasyprint documentation](./weasyprint.md).

## Creating Templates

Report and label templates are managed from the [Admin Center](../settings/admin.md#admin-center), which provides dedicated panels (under the *Reporting* group) for each template type:

- **Label Templates** - Create and edit [label templates](./labels.md)
- **Report Templates** - Create and edit [report templates](./report.md)
- **Report Snippets** - Manage reusable [snippet](#report-snippets) files
- **Report Assets** - Manage uploaded [asset](#report-assets) files

Label and report templates are created and edited using the built-in [template editor](./template_editor.md), which allows templates to be written directly within the browser, with a live preview of the rendered output.

!!! tip "Staff Access Only"
    Only users with staff access can create, upload or edit templates, snippets and assets.

!!! info "Backend Admin Interface"
    Templates can also be managed at a lower level via the [backend admin interface](../settings/admin.md#backend-admin-interface), under the *Report* section. This is recommended for advanced users only.

### Name and Description

Each report template requires a name and description, which identify and describe the report template.

### Revision

Each template has a revision number, which is automatically incremented each time the template is updated. This provides a simple mechanism for tracking changes to a template over time. The revision number is read-only, and cannot be edited directly.

!!! info "Template Revision Context"
    The revision number of the template is made available when rendering, via the `template_revision` [context variable](./context_variables.md#global-context).

### Enabled Status

Boolean field which determines if the specific report template is enabled, and available for use. Reports can be disabled to remove them from the list of available templates, but without deleting them from the database.

### Attach to Model

If the *Attach to Model on Print* option is enabled, a copy of the generated report is automatically saved as a file attachment against the item (model instance) for which it was generated, each time the template is printed.

!!! warning "Attachment Support"
    The report output is only attached if the target model type supports file attachments.

### Filename Pattern

The filename pattern used to generate the output `.pdf` file. Defaults to "report.pdf".

The filename pattern allows custom rendering with any context variables which are available to the report. For example, a test report for a particular [Stock Item](../stock/index.md#stock-item) can use the part name and serial number of the stock item when generating the report name:

{{ image("report/filename_pattern.png", "Report filename pattern") }}


### Template Filters

Each template instance provides a *filters* field, which can be used to filter which items a report or label template can be generated against. The target of the *filters* field depends on the model type associated with the particular template.

As an example, let's say that a certain `StockItem` report should only be generated for "trackable" stock items. A filter could easily be constructed to accommodate this, by limiting available items to those where the associated [Part](../part/index.md) is *trackable*:

{{ image("report/filters_valid.png", "Report filter selection") }}

If you enter an invalid option for the filter field, an error message will be displayed:

{{ image("report/filters_invalid.png", "Report filter error") }}

!!! warning "Advanced Users"
    Report filtering is an advanced topic, and requires a little bit of knowledge of the underlying data structure!

#### List Filtering

To filter a queryset against a list of ID values, you can use the following "list" syntax:

```
item__in=[1,2,3]
```

Note that:

- The list must be enclosed in square brackets `[]`
- The items in the list must be comma-separated
- The key must end with `__in` to indicate that it is a list filter (*note the double underscore*).

### Metadata

A JSON field made available to any [plugins](../plugins/index.md) - but not used by internal code.

## Reporting Options

A number of global reporting options are available for customizing InvenTree reports:

{{ image("report/report.png", "Report options") }}

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

User can upload asset files (e.g. images) which can be used when generating reports. For example, you may wish to generate a report with your company logo in the header.

Refer to the [report assets](./assets.md) documentation for further information.

## Report Snippets

InvenTree provides report "snippets" - reusable template files which cannot be rendered by themselves, but can be included in other templates.

Refer to the [report snippets](./snippets.md) documentation for further information.

## Security

Report templates are powerful by design — they have access to the full Django template language and to model data across the InvenTree database. For this reason, **template upload is restricted to staff users only**.

### URL Fetching

When WeasyPrint renders a template to PDF it can make outbound requests to load images, stylesheets, and fonts referenced in the HTML. InvenTree restricts this through a custom URL fetcher with the following rules:

| URL Type | Behavior |
|---|---|
| `data:` URIs | Always permitted — self-contained, no network access |
| `file://` | Always blocked — assets and images must be inlined as `data:` URIs before reaching WeasyPrint |
| `http` / `https` | Disabled by default, but can be enabled - see *Remote URL Fetching* below |
| Any other scheme | Always blocked |

HTTP redirects are also disabled: a URL that passes validation cannot redirect to an internal address.

### Remote URL Fetching

The **Report URL Fetching** system setting (`REPORT_FETCH_URLS`) controls whether `http://` and `https://` URLs in templates are permitted. It defaults to **disabled**.

When enabled, URLs are still validated against private, loopback, link-local, and reserved IP ranges before the request is made, preventing templates from being used as a vector for [Server-Side Request Forgery (SSRF)](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery) attacks against internal network services.

!!! warning "Enable with care"
    Enabling remote URL fetching allows report templates to trigger outbound HTTP requests from the InvenTree server. Only enable this if your templates genuinely require it, and ensure that templates are reviewed before deployment.

### Asset Files

[Asset files](./assets.md) uploaded through the admin interface are embedded directly into the rendered PDF as base64 `data:` URIs — they are read via the Django storage API and never loaded through WeasyPrint's URL fetcher. This means assets work correctly regardless of whether remote URL fetching is enabled, and also work with remote storage backends such as S3.

There are various [helper functions](./helpers.md#report-assets) available to assist with embedding assets into templates.
