---
title: Build Order Report
---

## Build Order Report

Custom build order reports may be generated against any given [Build Order](../build/build.md). For example, build order reports can be used to generate work orders.

### Build Filters

A build order report template may define a set of filters against which [Build Order](../build/build.md) items are sorted.

### Context Variables

In addition to the default report context variables, the following context variables are made available to the build order report template for rendering:

| Variable | Description |
| --- | --- |
| build | The build object the report is being generated against |
| part | The [Part](./context_variables.md#part) object that the build references |
| line_items | A shortcut for [build.line_items](#build) |
| bom_items | A shortcut for [build.bom_items](#build) |
| build_outputs | A shortcut for [build.build_outputs](#build) |
| reference | The build order reference string |
| quantity | Build order quantity (number of assemblies being built) |

#### build

The following variables are accessed by build.variable

| Variable | Description |
| --- | --- |
| active | Boolean that tells if the build is active |
| batch | Batch code transferred to build parts (optional) |
| line_items | A query set with all the build line items associated with the build |
| bom_items | A query set with all BOM items for the part being assembled |
| build_outputs | A queryset containing all build output ([Stock Item](../stock/stock.md)) objects associated with this build |
| can_complete | Boolean that tells if the build can be completed. Means: All material allocated and all parts have been build. |
| are_untracked_parts_allocated | Boolean that tells if all bom_items have allocated stock_items. |
| creation_date | Date where the build has been created |
| completion_date | Date the build was completed (or, if incomplete, the expected date of completion) |
| completed_by | The [User](./context_variables.md#user) that completed the build |
| is_overdue | Boolean that tells if the build is overdue |
| is_complete | Boolean that tells if the build is complete |
| issued_by | The [User](./context_variables.md#user) who created the build |
| link | External URL for extra information |
| notes | Text notes |
| parent | Reference to a parent build object if this is a sub build |
| part | The [Part](./context_variables.md#part) to be built (from component BOM items) |
| quantity | Build order quantity (total number of assembly outputs) |
| completed | The number out outputs which have been completed |
| reference | Build order reference (required, must be unique) |
| required_parts | A query set with all parts that are required for the build |
| responsible | Owner responsible for completing the build. This can be a user or a group. Depending on that further context variables differ |
| sales_order | References to a [Sales Order](./context_variables.md#salesorder) object for which this build is required (e.g. the output of this build will be used to fulfil a sales order) |
| status | The status of the build. 20 means 'Production' |
| sub_build_count | Number of sub builds |
| sub_builds | Query set with all sub builds |
| target_date | Date the build will be overdue |
| take_from | [StockLocation](./context_variables.md#stocklocation) to take stock from to make this build (if blank, can take from anywhere) |
| title | The full name of the build |
| description | The description of the build |
| allocated_stock.all | A query set with all allocated stock items for the build |

As usual items in a query sets can be selected by adding a .n to the set e.g. build.required_parts.0
will result in the first part of the list. Each query set has again its own context variables.

#### line_items

The `line_items` variable is a list of all build line items associated with the selected build. The following attributes are available for each individual line_item instance:

| Attribute | Description |
| --- | --- |
| .build | A reference back to the parent build order |
| .bom_item | A reference to the BOMItem which defines this line item |
| .quantity | The required quantity which is to be allocated against this line item |
| .part | A shortcut for .bom_item.sub_part |
| .allocations | A list of BuildItem objects which allocate stock items against this line item |
| .allocated_quantity | The total stock quantity which has been allocated against this line |
| .unallocated_quantity | The remaining quantity to allocate |
| .is_fully_allocated | Boolean value, returns True if the line item has sufficient stock allocated against it |
| .is_overallocated | Boolean value, returns True if the line item has more allocated stock than is required |

#### bom_items

| Attribute | Description |
| --- | --- |
| .reference | The reference designators of the components |
| .quantity | The number of components required to build |
| .overage | The extra amount required to assembly |
| .consumable | Boolean field, True if this is a "consumable" part which is not tracked through builds |
| .sub_part | The part at this position |
| .substitutes.all | A query set with all allowed substitutes for that part |
| .note | Extra text field which can contain additional information |


#### allocated_stock.all

| Attribute | Description |
| --- | --- |
| .bom_item | The bom item where this part belongs to |
| .stock_item | The allocated [StockItem](./context_variables.md#stockitem) |
| .quantity | The number of components needed for the build (components in BOM x parts to build) |

### Example

The following example will create a report with header and BOM. In the BOM table substitutes will be listed.

{% raw %}
```html
{% extends "report/inventree_report_base.html" %}

{% load i18n %}
{% load report %}
{% load barcode %}
{% load inventree_extras %}
{% load markdownify %}

{% block page_margin %}
margin: 2cm;
margin-top: 4cm;
{% endblock %}

{% block style %}

.header-right {
    text-align: right;
    float: right;
}

.logo {
    height: 20mm;
    vertical-align: middle;
}

.details {
    width: 100%;
    border: 1px solid;
    border-radius: 3px;
    padding: 5px;
    min-height: 42mm;
}

.details table {
    overflow-wrap: break-word;
    word-wrap: break-word;
    width: 65%;
    table-layout: fixed;
    font-size: 75%;
}
.changes table {
    overflow-wrap: break-word;
    word-wrap: break-word;
    width: 100%;
    table-layout: fixed;
    font-size: 75%;
    border: 1px solid;
}

.changes-table th {
    font-size: 100%;
    border: 1px solid;
}

.changes-table td {
    border: 1px solid;
}

.details table td:not(:last-child){
    white-space: nowrap;
}

.details table td:last-child{
    width: 50%;
    padding-left: 1cm;
    padding-right: 1cm;
}

.details-table td {
    padding-left: 10px;
    padding-top: 5px;
    padding-bottom: 5px;
    border-bottom: 1px solid #555;
}

{% endblock %}

{% block bottom_left %}
content: "v{{report_revision}} - {{ date.isoformat }}";
{% endblock %}

{% block header_content %}
    <!-- TODO - Make the company logo asset generic -->
    <img class='logo' src="{% asset 'company_logo.png' %}" alt="logo" width="150">

    <div class='header-right'>
        <h3>
            Build Order {{ build }}
        </h3>
        <br>
    </div>

    <hr>
{% endblock %}

{% block page_content %}

<div class='details'>

        <table class='details-table'>
            <tr>
                <th>{% trans "Build Order" %}</th>
                <td>{% internal_link build.get_absolute_url build %}</td>
            </tr>
            <tr>
                <th>{% trans "Order" %}</th>
                <td>{{ reference }}</td>
            </tr>
            <tr>
                <th>{% trans "Part" %}</th>
                <td>{% internal_link part.get_absolute_url part.IPN %}</td>
            </tr>
            <tr>
                <th>{% trans "Quantity" %}</th>
                <td>{{ build.quantity }}</td>
            </tr>
            <tr>
                <th>{% trans "Description" %}</th>
                <td>{{ build.title }}</td>
            </tr>
            <tr>
                <th>{% trans "Issued" %}</th>
                <td>{% render_date build.creation_date %}</td>
            </tr>
            <tr>
                <th>{% trans "Target Date" %}</th>
                <td>
                    {% if build.target_date %}
                    {% render_date build.target_date %}
                    {% else %}
                    <em>Not specified</em>
                    {% endif %}
                </td>
            </tr>
            {% if build.parent %}
            <tr>
                <th>{% trans "Required For" %}</th>
                <td>{% internal_link build.parent.get_absolute_url build.parent %}</td>
            </tr>
            {% endif %}
            {% if build.issued_by %}
            <tr>
                <th>{% trans "Issued By" %}</th>
                <td>{{ build.issued_by }}</td>
            </tr>
            {% endif %}
            {% if build.responsible %}
            <tr>
                <th>{% trans "Responsible" %}</th>
                <td>{{ build.responsible }}</td>
            </tr>
            {% endif %}
            <tr>
                <th>{% trans "Sub builds count" %}</th>
                <td>{{ build.sub_build_count }}</td>
            </tr>
	    {% if build.sub_build_count > 0 %}
            <tr>
                <th>{% trans "Sub Builds" %}</th>
                <td>{{ build.sub_builds }}</td>
            </tr>
            {% endif %}
            <tr>
                <th>{% trans "Overdue" %}</th>
                <td>{{ build.is_overdue }}</td>
            </tr>
            <tr>
                <th>{% trans "Can complete" %}</th>
                <td>{{ build.can_complete }}</td>
            </tr>
        </table>
</div>

<h3>{% trans "Notes" %}</h3>
{% if build.notes %}
{{ build.notes|markdownify }}
{% endif %}

<h3>{% trans "Parts" %}</h3>

<div class='changes'>
  <table class='changes-table'>
    <thead>
      <tr>
	<th>Original IPN</th>
	<th>Reference</th>
	<th>Replace width IPN</th>
      </tr>
    </thead>
    <tbody>
  {% for line in build.bom_items %}
      <tr>
	<td> {{ line.sub_part.IPN }} </td>
	<td> {{ line.reference }} </td>
	<td> {{ line.substitutes.all.0.part.IPN }} </td>
      </tr>
  {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
```

{% endraw %}

This will result a report page like this:

{% with id="report-options", url="build/report-61.png", description="Report Example Builds" %} {% include "img.html" %} {% endwith %}

### Default Report Template

A default *Build Report* template is provided out of the box, which is useful for generating simple test reports. Furthermore, it may be used as a starting point for developing custom BOM reports:

View the [source code](https://github.com/inventree/InvenTree/blob/master/InvenTree/report/templates/report/inventree_build_order_base.html) for the default build report template.
