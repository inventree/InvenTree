---
title: Reference Patterns
---

## Reference Patterns

InvenTree contains a number of data models which require a *unique* reference field (such as [Purchase Orders](../order/purchase_order.md)). In addition to being *unique* these reference values must conform to a specific *pattern* (which can be defined by the user). Defined reference patterns also make it simple for the user to control how references are generated.

### Default Patterns

Out of the box, InvenTree defines a standard "pattern" for each type of reference (which can be edited via the InvenTree [settings interface](./global.md)).

| Model Type | Default Pattern | Example Output |
| --- | --- | --- |
| Purchase Order | `{% raw %}PO-{ref:04d}{% endraw %}` | PO-0001 |
| Sales Order | `{% raw %}SO-{ref:04d}{% endraw %}` | SO-0123 |
| Build Order | `{% raw %}BO-{ref:04d}{% endraw %}` | BO-1234 |
| Return Order | `{% raw %} RMA-{ref:04d}{% endraw %}` | RMA-0987 |

### Pattern Requirements

Patterns can contain a mixture of literal strings, named variable blocks, and wildcard characters:

- The pattern **must** contain a single `{% raw %}{ref}{% endraw %}` variable - this is the required sequential part of the pattern
- A `?` (question mark) character is treated as a wildcard which will match any character
- A `#` (hash) character is treated as a wildcard which will match any digit `0-9`
- Any other characters will be matched literally

### Variables

When building a reference, the following variables are available for use:

| Variable | Description |
| --- | --- |
| `{% raw %}{ref}{% endraw %}` | Incrementing portion of the reference (**required*)). Determines which part of the reference field auto-increments |
| `{% raw %}{date}{% endraw %}` | The current date / time. This is a [Python datetime object](https://docs.python.org/3/library/datetime.html#datetime.datetime.now) |

The reference field pattern uses <a href="https://www.w3schools.com/python/ref_string_format.asp">Python string formatting</a> for value substitution.

!!! tip "Date Formatting"
    The `{% raw %}{date}{% endraw %}` variable can be formatted using the [Python Format Codes](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior).

#### Substitution Examples

Some examples below demonstrate how the variable substitution can be implemented:

| Pattern | Description | Example Output |
| --- | --- | --- |
| `{% raw %}PO-{ref}{% endraw %}` | Render the *reference* variable without any custom formatting | PO-123 |
| `{% raw %}PO-{ref:05d}{% endraw %}` | Render the *reference* variable as a 5-digit decimal number | PO-00123 |
| `{% raw %}PO-{ref:05d}-{date:%Y-%m-%d}{% endraw %}` | Render the *date* variable in isoformat | PO-00123-2023-01-17 |
