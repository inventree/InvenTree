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
