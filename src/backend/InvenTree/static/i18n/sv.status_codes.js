



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



/*
 * Status codes for the stock model.
 * Generated from the values specified in "status_codes.py"
 */
const stockCodes = {
    
    'OK': {
        key: 10,
        value: 'OK',
        label: 'bg-success',
    },
    
    'ATTENTION': {
        key: 50,
        value: 'OBS!',
        label: 'bg-warning',
    },
    
    'DAMAGED': {
        key: 55,
        value: 'Skadad',
        label: 'bg-warning',
    },
    
    'DESTROYED': {
        key: 60,
        value: 'Förstörd',
        label: 'bg-danger',
    },
    
    'REJECTED': {
        key: 65,
        value: 'Avvisad',
        label: 'bg-danger',
    },
    
    'LOST': {
        key: 70,
        value: 'Förlorad',
        label: 'bg-dark',
    },
    
    'QUARANTINED': {
        key: 75,
        value: 'I karantän',
        label: 'bg-info',
    },
    
    'RETURNED': {
        key: 85,
        value: 'Återlämnad',
        label: 'bg-warning',
    },
    
};

/*
 * Render the status for a stock object.
 * Uses the values specified in "status_codes.py"
 */
function stockStatusDisplay(key, options={}) {
    return renderStatusLabel(key, stockCodes, options);
}



/*
 * Status codes for the stockHistory model.
 * Generated from the values specified in "status_codes.py"
 */
const stockHistoryCodes = {
    
    'LEGACY': {
        key: 0,
        value: 'Spårningspost för äldre lager',
        label: 'bg-secondary',
    },
    
    'CREATED': {
        key: 1,
        value: 'Lagerpost skapad',
        label: 'bg-secondary',
    },
    
    'EDITED': {
        key: 5,
        value: 'Redigerade lagerpost',
        label: 'bg-secondary',
    },
    
    'ASSIGNED_SERIAL': {
        key: 6,
        value: 'Tilldelade serienummer',
        label: 'bg-secondary',
    },
    
    'STOCK_COUNT': {
        key: 10,
        value: 'Lagersaldo beräknat',
        label: 'bg-secondary',
    },
    
    'STOCK_ADD': {
        key: 11,
        value: 'Lagerpost manuellt tillagd',
        label: 'bg-secondary',
    },
    
    'STOCK_REMOVE': {
        key: 12,
        value: 'Lagerpost manuellt borttagen',
        label: 'bg-secondary',
    },
    
    'STOCK_MOVE': {
        key: 20,
        value: 'Platsen har ändrats',
        label: 'bg-secondary',
    },
    
    'STOCK_UPDATE': {
        key: 25,
        value: 'Stock updated',
        label: 'bg-secondary',
    },
    
    'INSTALLED_INTO_ASSEMBLY': {
        key: 30,
        value: 'Installerad i montering',
        label: 'bg-secondary',
    },
    
    'REMOVED_FROM_ASSEMBLY': {
        key: 31,
        value: 'Borttagen från montering',
        label: 'bg-secondary',
    },
    
    'INSTALLED_CHILD_ITEM': {
        key: 35,
        value: 'Installerat komponentobjekt',
        label: 'bg-secondary',
    },
    
    'REMOVED_CHILD_ITEM': {
        key: 36,
        value: 'Tog bort komponentobjekt',
        label: 'bg-secondary',
    },
    
    'SPLIT_FROM_PARENT': {
        key: 40,
        value: 'Dela från överordnat objekt',
        label: 'bg-secondary',
    },
    
    'SPLIT_CHILD_ITEM': {
        key: 42,
        value: 'Dela underordnat objekt',
        label: 'bg-secondary',
    },
    
    'MERGED_STOCK_ITEMS': {
        key: 45,
        value: 'Sammanfogade lagerposter',
        label: 'bg-secondary',
    },
    
    'CONVERTED_TO_VARIANT': {
        key: 48,
        value: 'Konverterad till variant',
        label: 'bg-secondary',
    },
    
    'BUILD_OUTPUT_CREATED': {
        key: 50,
        value: 'Bygg orderutgång skapad',
        label: 'bg-secondary',
    },
    
    'BUILD_OUTPUT_COMPLETED': {
        key: 55,
        value: 'Bygg orderutgång slutförd',
        label: 'bg-secondary',
    },
    
    'BUILD_OUTPUT_REJECTED': {
        key: 56,
        value: 'Build order output rejected',
        label: 'bg-secondary',
    },
    
    'BUILD_CONSUMED': {
        key: 57,
        value: 'Konsumeras av byggorder',
        label: 'bg-secondary',
    },
    
    'SHIPPED_AGAINST_SALES_ORDER': {
        key: 60,
        value: 'Shipped against Sales Order',
        label: 'bg-secondary',
    },
    
    'RECEIVED_AGAINST_PURCHASE_ORDER': {
        key: 70,
        value: 'Received against Purchase Order',
        label: 'bg-secondary',
    },
    
    'RETURNED_AGAINST_RETURN_ORDER': {
        key: 80,
        value: 'Returned against Return Order',
        label: 'bg-secondary',
    },
    
    'SENT_TO_CUSTOMER': {
        key: 100,
        value: 'Skickat till kund',
        label: 'bg-secondary',
    },
    
    'RETURNED_FROM_CUSTOMER': {
        key: 105,
        value: 'Returnerad från kund',
        label: 'bg-secondary',
    },
    
};

/*
 * Render the status for a stockHistory object.
 * Uses the values specified in "status_codes.py"
 */
function stockHistoryStatusDisplay(key, options={}) {
    return renderStatusLabel(key, stockHistoryCodes, options);
}



/*
 * Status codes for the build model.
 * Generated from the values specified in "status_codes.py"
 */
const buildCodes = {
    
    'PENDING': {
        key: 10,
        value: 'Väntar',
        label: 'bg-secondary',
    },
    
    'PRODUCTION': {
        key: 20,
        value: 'Produktion',
        label: 'bg-primary',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'On Hold',
        label: 'bg-warning',
    },
    
    'CANCELLED': {
        key: 30,
        value: 'Avbruten',
        label: 'bg-danger',
    },
    
    'COMPLETE': {
        key: 40,
        value: 'Slutför',
        label: 'bg-success',
    },
    
};

/*
 * Render the status for a build object.
 * Uses the values specified in "status_codes.py"
 */
function buildStatusDisplay(key, options={}) {
    return renderStatusLabel(key, buildCodes, options);
}



/*
 * Status codes for the purchaseOrder model.
 * Generated from the values specified in "status_codes.py"
 */
const purchaseOrderCodes = {
    
    'PENDING': {
        key: 10,
        value: 'Väntar',
        label: 'bg-secondary',
    },
    
    'PLACED': {
        key: 20,
        value: 'Placerad',
        label: 'bg-primary',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'On Hold',
        label: 'bg-warning',
    },
    
    'COMPLETE': {
        key: 30,
        value: 'Slutför',
        label: 'bg-success',
    },
    
    'CANCELLED': {
        key: 40,
        value: 'Avbruten',
        label: 'bg-danger',
    },
    
    'LOST': {
        key: 50,
        value: 'Förlorad',
        label: 'bg-warning',
    },
    
    'RETURNED': {
        key: 60,
        value: 'Återlämnad',
        label: 'bg-warning',
    },
    
};

/*
 * Render the status for a purchaseOrder object.
 * Uses the values specified in "status_codes.py"
 */
function purchaseOrderStatusDisplay(key, options={}) {
    return renderStatusLabel(key, purchaseOrderCodes, options);
}



/*
 * Status codes for the salesOrder model.
 * Generated from the values specified in "status_codes.py"
 */
const salesOrderCodes = {
    
    'PENDING': {
        key: 10,
        value: 'Väntar',
        label: 'bg-secondary',
    },
    
    'IN_PROGRESS': {
        key: 15,
        value: 'Pågående',
        label: 'bg-primary',
    },
    
    'SHIPPED': {
        key: 20,
        value: 'Skickad',
        label: 'bg-success',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'On Hold',
        label: 'bg-warning',
    },
    
    'COMPLETE': {
        key: 30,
        value: 'Slutför',
        label: 'bg-success',
    },
    
    'CANCELLED': {
        key: 40,
        value: 'Avbruten',
        label: 'bg-danger',
    },
    
    'LOST': {
        key: 50,
        value: 'Förlorad',
        label: 'bg-warning',
    },
    
    'RETURNED': {
        key: 60,
        value: 'Återlämnad',
        label: 'bg-warning',
    },
    
};

/*
 * Render the status for a salesOrder object.
 * Uses the values specified in "status_codes.py"
 */
function salesOrderStatusDisplay(key, options={}) {
    return renderStatusLabel(key, salesOrderCodes, options);
}



/*
 * Status codes for the returnOrder model.
 * Generated from the values specified in "status_codes.py"
 */
const returnOrderCodes = {
    
    'PENDING': {
        key: 10,
        value: 'Väntar',
        label: 'bg-secondary',
    },
    
    'IN_PROGRESS': {
        key: 20,
        value: 'Pågående',
        label: 'bg-primary',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'On Hold',
        label: 'bg-warning',
    },
    
    'COMPLETE': {
        key: 30,
        value: 'Slutför',
        label: 'bg-success',
    },
    
    'CANCELLED': {
        key: 40,
        value: 'Avbruten',
        label: 'bg-danger',
    },
    
};

/*
 * Render the status for a returnOrder object.
 * Uses the values specified in "status_codes.py"
 */
function returnOrderStatusDisplay(key, options={}) {
    return renderStatusLabel(key, returnOrderCodes, options);
}



/*
 * Status codes for the returnOrderLineItem model.
 * Generated from the values specified in "status_codes.py"
 */
const returnOrderLineItemCodes = {
    
    'PENDING': {
        key: 10,
        value: 'Väntar',
        label: 'bg-secondary',
    },
    
    'RETURN': {
        key: 20,
        value: 'Return',
        label: 'bg-success',
    },
    
    'REPAIR': {
        key: 30,
        value: 'Reparera',
        label: 'bg-primary',
    },
    
    'REPLACE': {
        key: 40,
        value: 'Ersätt',
        label: 'bg-warning',
    },
    
    'REFUND': {
        key: 50,
        value: 'Återbetala',
        label: 'bg-info',
    },
    
    'REJECT': {
        key: 60,
        value: 'Avvisa',
        label: 'bg-danger',
    },
    
};

/*
 * Render the status for a returnOrderLineItem object.
 * Uses the values specified in "status_codes.py"
 */
function returnOrderLineItemStatusDisplay(key, options={}) {
    return renderStatusLabel(key, returnOrderLineItemCodes, options);
}

