---
title: BOM Generation
---

## BOM Generation

The bill of materials is an essential part of the documentation that needs to be sent to the factory. A simple csv export is OK to be important into SMT machines. But for human readable documentation it might not be sufficient. Additional information is needed. The Inventree report system allows to generate BOM well formatted BOM reports.

### Context variables
| Variable | Description |
| --- | --- |
| bom_items | Query set that contains all BOM items |
| bom_items...sub_part | One component of the BOM |
| bom_items...quantity | Number of parts |
| bom_items...reference | Reference designators of the part |
| bom_items...substitutes | Query set that contains substitutes of the part if any exist in the BOM |

### Examples

#### BOM

The following picture shows a simple example for a PCB with just three components from two different parts.

{% with id="report-options", url="report/bom_example.png", description="BOM example" %} {% include 'img.html' %} {% endwith %}

This example has been created using the following html template:

```html
{% raw %}
{% extends "report/inventree_report_base.html" %}

{% load i18n %}
{% load report %}
{% load inventree_extras %}

{% block page_margin %}
margin-left: 2cm;
margin-right: 1cm;
margin-top: 4cm;
{% endblock %}

{% block bottom_left %}
content: "v{{report_revision}} - {{ date.isoformat }}";
{% endblock %}

{% block bottom_center %}
content: "InvenTree v{% inventree_version %}";
{% endblock %}

{% block style %}
.header-left {
    text-align: left;
    float: left;
}
table {
    border: 1px solid #eee;
    border-radius: 3px;
    border-collapse: collapse;
    width: 100%;
    font-size: 80%;
}
table td {
    border: 1px solid #eee;
}
{% endblock %}

{% block header_content %}
    <div class='header-left'>
        <h3>{% trans "Bill of Materials" %}</h3>
    </div>
{% endblock %}

{% block page_content %}
<table>
  <tr> <td>Board</td><td>{{ part.IPN }}</td>  </tr>
  <tr> <td>Description</td><td>{{ part.description }}</td> </tr>
  <tr> <td>User</td><td>{{ user }}</td> </tr>
  <tr> <td>Date</td><td>{{ date }}</td> </tr>
  <tr> <td>Number of different components (codes)</td><td>{{ bom_items.count }}</td> </tr>
</table>
<br>
<table class='table table-striped table-condensed'>
    <thead>
        <tr>
            <th>{% trans "IPN" %}</th>
            <th>{% trans "MPN" %}</th>
            <th>{% trans "Manufacturer" %}</th>
            <th>{% trans "Quantity" %}</th>
            <th>{% trans "Reference" %}</th>
            <th>{% trans "Substitute" %}</th>
        </tr>
    </thead>
    <tbody>
        {% for line in bom_items.all %}
          <tr>
            <td>{{ line.sub_part.IPN }}</td>
            <td>{{ line.sub_part.name }}</td>
	        <td>
	          {% for manf in line.sub_part.manufacturer_parts.all %}
               {{ manf.manufacturer.name }}
               {% endfor %}
          </td>
          <td>{% decimal line.quantity %}</td>
          <td>{{ line.reference }}</td>
	        <td>
	          {% for sub in line.substitutes.all %}
		    {{ sub.part.IPN }}<br>
            {% endfor %}
          </td>
          </tr>
        {% endfor %}
    </tbody>
</table>

{% endblock %}
{% endraw %}
```

#### Pick List

When all material has been allocated someone has to pick all things from the warehouse.
In case you need a printed pick list you can use the following template. This it just the
table. All other info and CSS has been left out for simplicity. Please have a look at the
BOM report for details.

{% raw %}
```html
<table class='changes-table'>
  <thead>
    <tr>
      <th>Original IPN</th>
      <th>Allocated Part</th>
      <th>Location</th>
      <th>PCS</th>
    </tr>
  </thead>
  <tbody>
  {% for line in build.allocated_stock.all %}
    <tr>
      <td> {{ line.bom_item.sub_part.IPN }} </td>
      {% if line.stock_item.part.IPN != line.bom_item.sub_part.IPN %}
        <td class='chg'> {{ line.stock_item.part.IPN }} </td>
      {% else %}
        <td> {{ line.stock_item.part.IPN }} </td>
      {% endif %}
      <td> {{ line.stock_item.location.pathstring }} </td>
      <td> {{ line.quantity }} </td>
    </tr>
  {% endfor %}
  </tbody>
</table>
```
{% endraw %}

Here we have a loop that runs through all allocated parts for the build. For each part
we list the original IPN from the BOM and the IPN of the allocated part. These can differ
in case you have substitutes or template/variants in the BOM. In case the parts differ
we use a different format for the table cell e.g. print bold font or red color.
For the picker we list the full path names of the stock locations and the quantity
that is needed for the build. This will result in the following printout:

{% with id="picklist", url="report/picklist.png", description="Picklist Example" %} {% include "img.html" %} {% endwith %}

For those of you who would like to replace the "/" by something else because it is hard
to read in some fonts use the following trick:

{% raw %}
```html
 <td> {% for loc in line.stock_item.location.path %}{{ loc.name }}{% if not forloop.last %}-{% endif %}{% endfor %} </td>
```
{% endraw %}

Here we use location.path which is a query set that contains the location path up to the
topmost parent. We use a loop to cycle through that and print the .name of the entry followed
by a "-". The foorloop.last is a Django trick that allows us to not print the "-" after
the last entry. The result looks like here:

{% with id="picklist_with_path", url="report/picklist_with_path.png", description="Picklist Example" %} {% include "img.html" %} {% endwith %}

Finally added a `{% raw %}|floatformat:0{% endraw %}` to the quantity that removes the trailing zeros.

### Default Report Template

A default *BOM Report* template is provided out of the box, which is useful for generating simple test reports. Furthermore, it may be used as a starting point for developing custom BOM reports:

View the [source code](https://github.com/inventree/InvenTree/blob/master/InvenTree/report/templates/report/inventree_bill_of_materials_report.html) for the default test report template.
