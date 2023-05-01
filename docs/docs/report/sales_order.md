---
title: Sales Order Reports
---

## Sales Order Reports

Custom sales order reports may be generated against any given [Sales Order](../order/sales_order.md). For example, a sales order report could be used to generate an invoice to send to a customer.

### Sales Order Filters

The report template can be filtered against available [Sales Order](../order/sales_order.md) instances.

### Context Variables

In addition to the default report context variables, the following variables are made available to the sales order report template for rendering:

| Variable | Description |
| --- | --- |
| order | The specific Sales Order object |
| reference | The order reference field (can also be accessed as `{% raw %}{{ order.description }}{% endraw %}`) |
| description | The order description field |
| customer | The [customer](../order/company.md#customers) associated with the particular sales order |
| lines | A list of available line items for this order |
| extra_lines | A list of available *extra* line items for this order |
| order.currency | The currency code associated with this order, e.g. 'CAD' |

### Default Report Template

A default *Sales Order Report* template is provided out of the box, which is useful for generating simple test reports. Furthermore, it may be used as a starting point for developing custom BOM reports:

View the [source code](https://github.com/inventree/InvenTree/blob/master/InvenTree/report/templates/report/inventree_so_report_base.html) for the default sales order report template.
