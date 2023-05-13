---
title: Stock Status
---

## Stock Status

Each [Stock Item](./stock.md#stock-item) has a *status* attribute, which serves to identify the current condition of the individual stock item.

Certain stock item status codes will restrict the availability of the stock item.

Below is the list of available stock status codes and their meaning:

| Status      | Description | Available |
| ----------- | ----------- | --- |
| <span class='badge inventree success'>OK</span> | Stock item is healthy, nothing wrong to report | <span class='badge inventree success'>Yes</span> |
| <span class='badge inventree warning'>Attention needed</span> | Stock item hasn't been checked or tested yet | <span class='badge inventree success'>Yes</span> |
| <span class='badge inventree warning'>Damaged</span> | Stock item is not functional in its present state | <span class='badge inventree success'>Yes</span> |
| <span class='badge inventree danger'>Destroyed</span> | Stock item has been destroyed | <span class='badge inventree danger'>No</span> |
| <span class='badge inventree'>Lost</span> | Stock item has been lost | <span class='badge inventree danger'>No</span> |
| <span class='badge inventree danger'>Rejected</span> | Stock item did not pass the quality control standards | <span class='badge inventree danger'>No</span> |
| <span class='badge inventree info'>Quarantined</span> | Stock item has been intentionally isolated and it unavailable | <span class='badge inventree danger'>No</span> |

The *status* of a given stock item is displayed on the stock item detail page:

{% with id="stock_status_label", url="stock/stock_status_label.png", description="Stock Status Label" %}
{% include 'img.html' %}
{% endwith %}

### Default Status Code

The default status code for any newly created Stock Item is <span class='badge inventree success'>OK</span>

## Update Status

To update the status code for an individual stock item, open the *Edit Stock Item* dialog and then select the required status code in the *Status* field

{% with id="stock_status_edit", url="stock/stock_status_edit.png", description="Edit stock item status" %}
{% include 'img.html' %}
{% endwith %}
