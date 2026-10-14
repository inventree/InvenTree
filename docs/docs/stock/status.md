---
title: Stock Status
---

## Stock Status

Each [Stock Item](./index.md#stock-item) has a *status* attribute, which serves to identify the current condition of the individual stock item.

Certain stock item status codes will restrict the availability of the stock item.

Below is the list of available stock status codes and their meaning:

{{ statuscodes("StockStatus") }}

Of these, only *OK*, *Attention needed*, *Damaged* and *Returned* count as "available" stock - the remainder are excluded from availability calculations.

The *status* of a given stock item is displayed on the stock item detail page:

{{ image("stock/stock_status_label.png", title="Stock status label") }}

### Custom Status Codes

Stock Status supports [custom states](../concepts/custom_states.md).

### Default Status Code

The default status code for any newly created Stock Item is <span class='badge inventree success'>OK</span>

## Update Status

To update the status code for an individual stock item, open the *Edit Stock Item* dialog and then select the required status code in the *Status* field

{{ image("stock/stock_status_edit.png", title="Edit stock item status") }}
