---
title: Test Report
---

## Test Report

InvenTree provides [test result](../stock/test.md) tracking functionality which allows the users to keep track of any tests which have been performed on a given [stock item](../stock/stock.md).

Custom test reports may be generated against any given stock item. All testing data is made available to the template for custom rendering as required.

For example, an "Acceptance Test" report template may be customized to the particular device, with the results for certain tests rendering in a particular part of the page, with any tests which have not passed highlighted.

### Stock Item Filters

A TestReport template may define a set of filters against which stock items are sorted. Any [StockItem](../stock/stock.md) objects which match the provided filters can use the given TestReport.

This allows each TestReport to easily be assigned to a particular StockItem, or even multiple items.

In the example below, a test report template is uploaded and available to any stock items linked to a part with the name *"My Widget"*. Any combination of fields relevant to the StockItem model can be used here.

{% with id="test-report-filters", url="report/test_report_filters.png", description="Test report filters" %}
{% include 'img.html' %}
{% endwith %}


### Context Variables

In addition to the default report context variables, the following context variables are made available to the TestReport template for rendering:

| Variable | Description |
| --- | --- |
| stock_item | The individual [Stock Item](./context_variables.md#stockitem) object for which this test report is being generated |
| serial | The serial number of the linked Stock Item |
| part | The [Part](./context_variables.md#part) object of which the stock_item is an instance |
| parameters | A dict object representing the [parameters](../part/parameter.md) of the referenced part |
| test_keys | A list of the available 'keys' for the test results recorded against the stock item |
| test_template_list | A list of the available [test templates](../part/test.md#part-test-templates) for the referenced part |
| test_template_map | A map / dict of the available test templates |
| results | A dict of test result objects, where the 'key' for each test result is a shortened version of the test name (see below) |
| result_list | A list of each test result object |
| installed_items | A flattened list representing all [Stock Item](./context_variables.md#stockitem) objects which are *installed inside* the referenced [Stock Item](./context_variables.md#stockitem) object |

#### Results

The *results* context variable provides a very convenient method of callout out a particular test result by name.

#### Example

Say for example that a Part "Electronic Widget" has a stock item with serial number #123, and has a test result uploaded called "Firmware Checksum". The templated file can reference this data as follows:

``` html
<h3>Part: {% raw %}{{ part.name }}{% endraw %}</h3>
<b>Serial Number: {% raw %}{{ stock_item.serial }}{% endraw %}</b>
<hr>
<p>
Firmware Checksum: {% raw %}{{ results.firmwarechecksum.value }}.
Uploaded by {{ results.firmwarechecksum.user }}{% endraw %}
</p>
```

#### Installed Items

The *installed_items* context variable is a list of all [StockItem](./context_variables.md#stockitem) instances which are installed inside the [StockItem](./context_variables.md#stockitem) referenced by the report template. Each [StockItem](./context_variables.md#stockitem) can be dereferenced as follows:

```html
{% raw %}
<table>
    {% for sub_item in installed_items %}
    <tr>
        <td>{{ sub_item.full_name }}</td>
        <td>Serial Number: {{ sub_item.serial }}</td>
        <td>Pass: {{ sub_item.passedAllRequiredTests }}</td>
    </tr>
    {% endfor %}
</table>
{% endraw %}
```

### Default Report Template

A default *Test Report* template is provided out of the box, which is useful for generating simple test reports. Furthermore, it may be used as a starting point for developing custom test reports:

{% with id="test-report-example", url="report/test_report_example.png", description="Example Test Report" %}
{% include "img.html" %}
{% endwith %}

View the [source code](https://github.com/inventree/InvenTree/blob/master/InvenTree/report/templates/report/inventree_test_report_base.html) for the default test report template.
