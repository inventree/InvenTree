---
title: Purchase Order Report
---

## Purchase Order Reports

Custom purchase order reports may be generated against any given [Purchase Order](../order/purchase_order.md). For example, purchase order reports could be used to generate a pdf of the order to send to a supplier.

### Purchase Order Filters

The report template can be filtered against available [Purchase Order](../order/purchase_order.md) instances.

### Context Variables

In addition to the default report context variables, the following variables are made available to the purchase order report template for rendering:

| Variable | Description |
| --- | --- |
| order | The specific Purchase Order object |
| reference | The order reference field (can also be accessed as `{% raw %}{{ order.reference }}{% endraw %}`) |
| description | The order description field |
| supplier | The [supplier](../order/company.md#suppliers) associated with this purchase order |
| lines | A list of available line items for this order |
| extra_lines | A list of available *extra* line items for this order |
| order.created_by | The user who created the order |
| order.responsible | The user or group who is responsible for the order |
| order.creation_date | The date when the order was created |
| order.target_date | The date when the order should arrive |
| order.if_overdue | Boolean value that tells if the target date has passed |
| order.currency | The currency code associated with this order, e.g. 'AUD' |
| order.contact | The [contact](./context_variables.md#contact)  object associated with this order |

#### Lines

Each line item (available within the `lines` list) has sub variables, as follows:

| Variable | Description |
| --- | --- |
| quantity | The quantity of the part to be ordered |
| part | The [supplierpart ](./context_variables.md#supplierpart) object to be ordered |
| reference | The reference given in the part of the order |
| notes | The notes given in the part of the order |
| target_date | The date when the part should arrive. Each part can have an individual date |
| price | The unit price the line item |
| total_line_price | The total price for this line item, calculated from the unit price and quantity |
| destination | The stock location where the part will be stored |

A simple example below shows how to use the context variables for each line item:

```html
{% raw %}
{% for line in lines %}
Internal Part: {{ line.part.part.name }} - <i>{{ line.part.part.description }}</i>
SKU: {{ line.part.SKU }}
Price: {% render_currency line.total_line_price %}
{% endfor %}
{% endraw %}
```


### Default Report Template

A default *Purchase Order Report* template is provided out of the box, which is useful for generating simple test reports. Furthermore, it may be used as a starting point for developing custom BOM reports:

View the [source code](https://github.com/inventree/InvenTree/blob/master/InvenTree/report/templates/report/inventree_po_report_base.html) for the default purchase order report template.
