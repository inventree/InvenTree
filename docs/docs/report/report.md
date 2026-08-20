---
title: Report and LabelGeneration
---

## Custom Reports

InvenTree supports a customizable reporting ecosystem, allowing the user to develop document templates that meet their particular needs.

PDF files are generated from custom HTML template files which are written by the user.

Templates can be used to generate *reports* or *labels* which can be  used in a variety of situations to format data in a friendly format for printing, distribution, conformance and testing.

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

## Merging Reports

When rendering reports for multiple items, the default behaviour is that each item is rendered as a separate report. The chosen templeate is rendered multiple times, once for each item selected, and expects a single item in the context variable.

However, it is possible to merge multiple items into a single report document. This is achieved by enabling the `merge` attribute of the report template:

{{ image("report/report_merge.png", alt="Report Merge Option") }}

When the `merge` is enabled, all selected items are passed to the report template in the `instances` context variable, which is a list of all selected items. The user can then iterate over this list to render multiple items in a single report document.

### Instance Context

When rendering a single template against multiple *instances* of a particular model (e.g. multiple parts, multiple stock items, etc), each instance being rendered has its own unique context data.

Each "instance" is provided to the report template as a dictionary of context variables, which can be accessed using standard django template syntax.

Refer to the [context variable documentation](./context_variables.md) for more information about the available context variables for each model type.

The `instances` variable is provided as a list of all selected items, where each item in the list is a dictionary of context variables for that particular instance. Within the report template, the user can iterate over the `instances` list to render each item in turn.

### Example

As an example, let's consider a report template where we are printing multiple parts in a single report document.

When the `merge` option is enabled, the report template is provided with an `instances` variable, which is a list of all selected parts.

Each *instance* in the `instances` list is a dictionary of context variables for that particular part, which conforms to the standard [part context structure](./context_variables.md#part).

```django
{% raw %}

{% for instance in instances %}
Part Name: {{ instance.part.name }} <br>
IPN: {{ instance.part.IPN }} <br>
Description: {{ instance.part.description }} <br>

{% endraw %}
```

!!! tip "Instance Prefix"
    Note that the context variable is prefixed with `instance.` when accessing variables for each item in the `instances` list.
