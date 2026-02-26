---
title: Stock Status
---

## Stock Status

Each [Stock Item](./index.md#stock-item) has a *status* attribute, which serves to identify the current condition of the individual stock item.

Certain stock item status codes will restrict the availability of the stock item.

Below is the list of available stock status codes and their meaning:

| Status | Description | Available |
| ----------- | ----------- | --- |
| <span class='badge inventree success'>OK</span> | Stock item is healthy, nothing wrong to report | <span class='badge inventree success'>Yes</span> |
| <span class='badge inventree warning'>Attention needed</span> | Stock item hasn't been checked or tested yet | <span class='badge inventree success'>Yes</span> |
| <span class='badge inventree warning'>Damaged</span> | Stock item is not functional in its present state | <span class='badge inventree success'>Yes</span> |
| <span class='badge inventree danger'>Destroyed</span> | Stock item has been destroyed | <span class='badge inventree danger'>No</span> |
| <span class='badge inventree'>Lost</span> | Stock item has been lost | <span class='badge inventree danger'>No</span> |
| <span class='badge inventree danger'>Rejected</span> | Stock item did not pass the quality control standards | <span class='badge inventree danger'>No</span> |
| <span class='badge inventree info'>Quarantined</span> | Stock item has been intentionally isolated and it unavailable | <span class='badge inventree danger'>No</span> |

The *status* of a given stock item is displayed on the stock item detail page:

{{ image("stock/stock_status_label.png", title="Stock status label") }}

**Source Code**

Refer to the source code for the Stock status codes:

::: stock.status_codes.StockStatus
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []

### Custom Status Codes

Stock Status supports [custom states](../concepts/custom_states.md).

### Default Status Code

The default status code for any newly created Stock Item is <span class='badge inventree success'>OK</span>

## Update Status

To update the status code for an individual stock item, open the *Edit Stock Item* dialog and then select the required status code in the *Status* field

{{ image("stock/stock_status_edit.png", title="Edit stock item status") }}
