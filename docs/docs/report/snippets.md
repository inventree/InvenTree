---
title: Report Snippets
---

## Report Snippets

A powerful feature provided by the django / WeasyPrint templating framework is the ability to include external template files. This allows commonly used template features to be broken out into separate files and reused across multiple templates.

To support this, InvenTree provides report "snippets" - short (or not so short) template files which cannot be rendered by themselves, but can be called from other templates.

Snippet files are managed from the [Admin Center](../settings/admin.md#admin-center), via the *Report Snippets* panel. Staff users can upload new snippet files, and edit or remove existing snippets.

Additionally, the content of an existing snippet can be modified directly within the browser - simply select a snippet from the table to open it in the built-in [template editor](./template_editor.md#editing-snippets).

Snippets are included in a template as follows:

```
{% raw %}{% include 'snippets/<snippet_name.html>' %}{% endraw %}
```

For example, consider a custom stocktake report for a particular stock location, where we wish to render a table with a row for each item in that location.

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
