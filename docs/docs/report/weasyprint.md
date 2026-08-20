---
title: Weasyprint Templates
---

## WeasyPrint Templates

We use the powerful [WeasyPrint](https://weasyprint.org/) PDF generation engine to create custom reports and labels.

!!! info "WeasyPrint"
    WeasyPrint is an extremely powerful and flexible reporting library. Refer to the [WeasyPrint docs](https://doc.courtbouillon.org/weasyprint/stable/) for further information.

### Stylesheets

Templates are rendered using standard HTML / CSS - if you are familiar with web page layout, you're ready to go!

HTML form elements (`input`, `select`, `textarea`, `button`) are converted into PDF form controls. Use CSS to limit which elements are converted; refer to the
[WeasyPrint docs](https://doc.courtbouillon.org/weasyprint/stable/common_use_cases.html#include-pdf-forms) for further information.

### Template Language

Uploaded report template files are passed through the [django template rendering framework]({% include "django.html" %}/topics/templates/), and as such accept the same variable template strings as any other django template file. Different variables are passed to the report template (based on the context of the report) and can be used to customize the contents of the generated PDF.

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
{% load l10n %}
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

!!! tip "l10n"
    You will need to add `{% raw %}{% load l10n %}{% endraw %}` to the top of your template file to use the `{% raw %}{% localize %}{% endraw %}` tag.
