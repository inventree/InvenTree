



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
        value: 'Uredu',
        label: 'bg-success',
    },
    
    'ATTENTION': {
        key: 50,
        value: 'Potrebna pažnja',
        label: 'bg-warning',
    },
    
    'DAMAGED': {
        key: 55,
        value: 'Oštećeno',
        label: 'bg-warning',
    },
    
    'DESTROYED': {
        key: 60,
        value: 'Uništeno',
        label: 'bg-danger',
    },
    
    'REJECTED': {
        key: 65,
        value: 'Odbijeno',
        label: 'bg-danger',
    },
    
    'LOST': {
        key: 70,
        value: 'Izgubljeno',
        label: 'bg-dark',
    },
    
    'QUARANTINED': {
        key: 75,
        value: 'U karantinu',
        label: 'bg-info',
    },
    
    'RETURNED': {
        key: 85,
        value: 'Vraćeno',
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
        value: 'Nasleđeni unos za praćenje zaliha',
        label: 'bg-secondary',
    },
    
    'CREATED': {
        key: 1,
        value: 'Stavka na zalihi stvorena',
        label: 'bg-secondary',
    },
    
    'EDITED': {
        key: 5,
        value: 'Izmenjena stavka u zalihama',
        label: 'bg-secondary',
    },
    
    'ASSIGNED_SERIAL': {
        key: 6,
        value: 'Dodeljen serijski broj',
        label: 'bg-secondary',
    },
    
    'STOCK_COUNT': {
        key: 10,
        value: 'Zalihe prebrojane',
        label: 'bg-secondary',
    },
    
    'STOCK_ADD': {
        key: 11,
        value: 'Zalihe dodane ručno',
        label: 'bg-secondary',
    },
    
    'STOCK_REMOVE': {
        key: 12,
        value: 'Zaliha ručno uklonjena',
        label: 'bg-secondary',
    },
    
    'STOCK_MOVE': {
        key: 20,
        value: 'Lokacija promenjena',
        label: 'bg-secondary',
    },
    
    'STOCK_UPDATE': {
        key: 25,
        value: 'Zaliha obnovljena',
        label: 'bg-secondary',
    },
    
    'INSTALLED_INTO_ASSEMBLY': {
        key: 30,
        value: 'Instalisan u sklopu',
        label: 'bg-secondary',
    },
    
    'REMOVED_FROM_ASSEMBLY': {
        key: 31,
        value: 'Skinuto sa sklopa',
        label: 'bg-secondary',
    },
    
    'INSTALLED_CHILD_ITEM': {
        key: 35,
        value: 'Instalirana stavka komponente',
        label: 'bg-secondary',
    },
    
    'REMOVED_CHILD_ITEM': {
        key: 36,
        value: 'Uklonjena stavka komponente',
        label: 'bg-secondary',
    },
    
    'SPLIT_FROM_PARENT': {
        key: 40,
        value: 'Odvoj od nadređene stavke',
        label: 'bg-secondary',
    },
    
    'SPLIT_CHILD_ITEM': {
        key: 42,
        value: 'Podeli podređenu stavku',
        label: 'bg-secondary',
    },
    
    'MERGED_STOCK_ITEMS': {
        key: 45,
        value: 'Spojene stavke zaliha',
        label: 'bg-secondary',
    },
    
    'CONVERTED_TO_VARIANT': {
        key: 48,
        value: 'Pretvoreno u varijaciju',
        label: 'bg-secondary',
    },
    
    'BUILD_OUTPUT_CREATED': {
        key: 50,
        value: 'Build order output created',
        label: 'bg-secondary',
    },
    
    'BUILD_OUTPUT_COMPLETED': {
        key: 55,
        value: 'Build order output completed',
        label: 'bg-secondary',
    },
    
    'BUILD_OUTPUT_REJECTED': {
        key: 56,
        value: 'Build order output rejected',
        label: 'bg-secondary',
    },
    
    'BUILD_CONSUMED': {
        key: 57,
        value: 'Consumed by build order',
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
        value: 'Sent to customer',
        label: 'bg-secondary',
    },
    
    'RETURNED_FROM_CUSTOMER': {
        key: 105,
        value: 'Returned from customer',
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
        value: 'Na čekanju',
        label: 'bg-secondary',
    },
    
    'PRODUCTION': {
        key: 20,
        value: 'Production',
        label: 'bg-primary',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'On Hold',
        label: 'bg-warning',
    },
    
    'CANCELLED': {
        key: 30,
        value: 'Otkazano',
        label: 'bg-danger',
    },
    
    'COMPLETE': {
        key: 40,
        value: 'Gotovo',
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
        value: 'Na čekanju',
        label: 'bg-secondary',
    },
    
    'PLACED': {
        key: 20,
        value: 'Postavljen',
        label: 'bg-primary',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'On Hold',
        label: 'bg-warning',
    },
    
    'COMPLETE': {
        key: 30,
        value: 'Gotovo',
        label: 'bg-success',
    },
    
    'CANCELLED': {
        key: 40,
        value: 'Otkazano',
        label: 'bg-danger',
    },
    
    'LOST': {
        key: 50,
        value: 'Izgubljeno',
        label: 'bg-warning',
    },
    
    'RETURNED': {
        key: 60,
        value: 'Vraćeno',
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
        value: 'Na čekanju',
        label: 'bg-secondary',
    },
    
    'IN_PROGRESS': {
        key: 15,
        value: 'U progresu',
        label: 'bg-primary',
    },
    
    'SHIPPED': {
        key: 20,
        value: 'Poslato',
        label: 'bg-success',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'On Hold',
        label: 'bg-warning',
    },
    
    'COMPLETE': {
        key: 30,
        value: 'Gotovo',
        label: 'bg-success',
    },
    
    'CANCELLED': {
        key: 40,
        value: 'Otkazano',
        label: 'bg-danger',
    },
    
    'LOST': {
        key: 50,
        value: 'Izgubljeno',
        label: 'bg-warning',
    },
    
    'RETURNED': {
        key: 60,
        value: 'Vraćeno',
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
        value: 'Na čekanju',
        label: 'bg-secondary',
    },
    
    'IN_PROGRESS': {
        key: 20,
        value: 'U progresu',
        label: 'bg-primary',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'On Hold',
        label: 'bg-warning',
    },
    
    'COMPLETE': {
        key: 30,
        value: 'Gotovo',
        label: 'bg-success',
    },
    
    'CANCELLED': {
        key: 40,
        value: 'Otkazano',
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
        value: 'Na čekanju',
        label: 'bg-secondary',
    },
    
    'RETURN': {
        key: 20,
        value: 'Return',
        label: 'bg-success',
    },
    
    'REPAIR': {
        key: 30,
        value: 'Repair',
        label: 'bg-primary',
    },
    
    'REPLACE': {
        key: 40,
        value: 'Replace',
        label: 'bg-warning',
    },
    
    'REFUND': {
        key: 50,
        value: 'Refund',
        label: 'bg-info',
    },
    
    'REJECT': {
        key: 60,
        value: 'Reject',
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

