{% load i18n %}
{% load status_codes %}
{% load inventree_extras %}

/* globals
*/

/* exported
    buildStatusDisplay,
    purchaseOrderStatusDisplay,
    returnOrderStatusDisplay,
    returnOrderLineItemStatusDisplay,
    salesOrderStatusDisplay,
    stockHistoryStatusDisplay,
    stockStatusDisplay,
*/

{% include "status_codes.html" with label='stock' options=StockStatus.list %}
{% include "status_codes.html" with label='stockHistory' options=StockHistoryCode.list %}
{% include "status_codes.html" with label='build' options=BuildStatus.list %}
{% include "status_codes.html" with label='purchaseOrder' options=PurchaseOrderStatus.list %}
{% include "status_codes.html" with label='salesOrder' options=SalesOrderStatus.list %}
{% include "status_codes.html" with label='returnOrder' options=ReturnOrderStatus.list %}
{% include "status_codes.html" with label='returnOrderLineItem' options=ReturnOrderLineStatus.list %}
