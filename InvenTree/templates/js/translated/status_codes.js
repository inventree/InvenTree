{% load i18n %}
{% load generic %}
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


/*
 * Generic function to render a status label
 */
function renderStatusLabel(key, codes, options={}) {

    let text = null;
    let label = null;

    // Find the entry which matches the provided key
    for (var name in codes) {
        let entry = codes[name];

        if (entry.key == key) {
            text = entry.value;
            label = entry.label;
            break;
        }
    }

    if (!text) {
        console.error(`renderStatusLabel could not find match for code ${key}`);
    }

    // Fallback for color
    label = label || 'bg-dark';

    if (!text) {
        text = key;
    }

    let classes = `badge rounded-pill ${label}`;

    if (options.classes) {
        classes += ` ${options.classes}`;
    }

    return `<span class='${classes}'>${text}</span>`;
}

{% include "status_codes.html" with label='stock' data=StockStatus.list %}
{% include "status_codes.html" with label='stockHistory' data=StockHistoryCode.list %}
{% include "status_codes.html" with label='build' data=BuildStatus.list %}
{% include "status_codes.html" with label='purchaseOrder' data=PurchaseOrderStatus.list %}
{% include "status_codes.html" with label='salesOrder' data=SalesOrderStatus.list %}
{% include "status_codes.html" with label='returnOrder' data=ReturnOrderStatus.list %}
{% include "status_codes.html" with label='returnOrderLineItem' data=ReturnOrderLineStatus.list %}
