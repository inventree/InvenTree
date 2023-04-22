---
title: Stock Status
---

## Stock Status

Stock status serves at categorizing and identifying the state of stock items.

Below is the current list of stock status and their proposed meaning:

| Status      | Description |
| ----------- | ----------- |
| OK | Stock item is healthy, nothing wrong to report |
| Attention needed | Stock item hasn't been checked or tested yet |
| Damaged | Stock item is not functional in its present state |
| Destroyed | Stock item has been destroyed |
| Lost | Stock item has been lost |
| Rejected | Stock item did not pass the quality control standards |
| Returned | Stock item was returned to seller (if bought) or is a customer return (if sold) |
| Quarantined | Stock item has been intentionally isolated and it unavailable |

Stock status code will remove the stock from certain operations. For instance, users can't add "destroyed" or "lost" stock to a sales order.

The stock status is displayed as a label in the header of each stock item detail page, for instance here the stock status is "OK":

{% with id="stock_status_label", url="stock/stock_status_label.png", description="Stock Status Label" %}
{% include 'img.html' %}
{% endwith %}

## Update Status

In the "Stock" tab of the part view, select all stock items which stock status needs to be updated:

{% with id="stock_status_change_multiple", url="stock/stock_status_change_multiple.png", description="Stock Status Status Multiple" %}
{% include 'img.html' %}
{% endwith %}

Click on `Stock Options > Change stock status`, select the new status then submit. All selected stock items status will be automatically updated:

{% with id="stock_status_change_multiple_done", url="stock/stock_status_change_multiple_done.png", description="Stock Status Status Multiple Done" %}
{% include 'img.html' %}
{% endwith %}
