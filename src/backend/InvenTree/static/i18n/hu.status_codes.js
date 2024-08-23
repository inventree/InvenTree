



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
        value: 'Rendben',
        label: 'bg-success',
    },
    
    'ATTENTION': {
        key: 50,
        value: 'Ellenőrizendő',
        label: 'bg-warning',
    },
    
    'DAMAGED': {
        key: 55,
        value: 'Sérült',
        label: 'bg-warning',
    },
    
    'DESTROYED': {
        key: 60,
        value: 'Megsemmisült',
        label: 'bg-danger',
    },
    
    'REJECTED': {
        key: 65,
        value: 'Elutasított',
        label: 'bg-danger',
    },
    
    'LOST': {
        key: 70,
        value: 'Elveszett',
        label: 'bg-dark',
    },
    
    'QUARANTINED': {
        key: 75,
        value: 'Karanténban',
        label: 'bg-info',
    },
    
    'RETURNED': {
        key: 85,
        value: 'Visszaküldve',
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
        value: 'Örökölt készlet követési bejegyzés',
        label: 'bg-secondary',
    },
    
    'CREATED': {
        key: 1,
        value: 'Készlet tétel létrehozva',
        label: 'bg-secondary',
    },
    
    'EDITED': {
        key: 5,
        value: 'Szerkeszett készlet tétel',
        label: 'bg-secondary',
    },
    
    'ASSIGNED_SERIAL': {
        key: 6,
        value: 'Hozzárendelt sorozatszám',
        label: 'bg-secondary',
    },
    
    'STOCK_COUNT': {
        key: 10,
        value: 'Készlet leleltározva',
        label: 'bg-secondary',
    },
    
    'STOCK_ADD': {
        key: 11,
        value: 'Készlet manuálisan hozzáadva',
        label: 'bg-secondary',
    },
    
    'STOCK_REMOVE': {
        key: 12,
        value: 'Készlet manuálisan elvéve',
        label: 'bg-secondary',
    },
    
    'STOCK_MOVE': {
        key: 20,
        value: 'Hely megváltozott',
        label: 'bg-secondary',
    },
    
    'STOCK_UPDATE': {
        key: 25,
        value: 'Készletadatok frissítve',
        label: 'bg-secondary',
    },
    
    'INSTALLED_INTO_ASSEMBLY': {
        key: 30,
        value: 'Gyártmányba beépült',
        label: 'bg-secondary',
    },
    
    'REMOVED_FROM_ASSEMBLY': {
        key: 31,
        value: 'Gyártmányból eltávolítva',
        label: 'bg-secondary',
    },
    
    'INSTALLED_CHILD_ITEM': {
        key: 35,
        value: 'Beépült összetevő tétel',
        label: 'bg-secondary',
    },
    
    'REMOVED_CHILD_ITEM': {
        key: 36,
        value: 'Eltávolított összetevő tétel',
        label: 'bg-secondary',
    },
    
    'SPLIT_FROM_PARENT': {
        key: 40,
        value: 'Szülő tételből szétválasztva',
        label: 'bg-secondary',
    },
    
    'SPLIT_CHILD_ITEM': {
        key: 42,
        value: 'Szétválasztott gyermek tétel',
        label: 'bg-secondary',
    },
    
    'MERGED_STOCK_ITEMS': {
        key: 45,
        value: 'Összevont készlet tétel',
        label: 'bg-secondary',
    },
    
    'CONVERTED_TO_VARIANT': {
        key: 48,
        value: 'Alkatrészváltozattá alakítva',
        label: 'bg-secondary',
    },
    
    'BUILD_OUTPUT_CREATED': {
        key: 50,
        value: 'Gyártási utasítás kimenete elkészült',
        label: 'bg-secondary',
    },
    
    'BUILD_OUTPUT_COMPLETED': {
        key: 55,
        value: 'Gyártási utasítás kimenete kész',
        label: 'bg-secondary',
    },
    
    'BUILD_OUTPUT_REJECTED': {
        key: 56,
        value: 'Gyártási utasítás kimenete elutasítva',
        label: 'bg-secondary',
    },
    
    'BUILD_CONSUMED': {
        key: 57,
        value: 'Gyártásra felhasználva',
        label: 'bg-secondary',
    },
    
    'SHIPPED_AGAINST_SALES_ORDER': {
        key: 60,
        value: 'Vevői rendelésre kiszállítva',
        label: 'bg-secondary',
    },
    
    'RECEIVED_AGAINST_PURCHASE_ORDER': {
        key: 70,
        value: 'Megrendelésre érkezett',
        label: 'bg-secondary',
    },
    
    'RETURNED_AGAINST_RETURN_ORDER': {
        key: 80,
        value: 'Visszavéve',
        label: 'bg-secondary',
    },
    
    'SENT_TO_CUSTOMER': {
        key: 100,
        value: 'Vevőnek kiszállítva',
        label: 'bg-secondary',
    },
    
    'RETURNED_FROM_CUSTOMER': {
        key: 105,
        value: 'Vevőtől visszaérkezett',
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
        value: 'Függőben',
        label: 'bg-secondary',
    },
    
    'PRODUCTION': {
        key: 20,
        value: 'Folyamatban',
        label: 'bg-primary',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'Felfüggesztve',
        label: 'bg-warning',
    },
    
    'CANCELLED': {
        key: 30,
        value: 'Törölve',
        label: 'bg-danger',
    },
    
    'COMPLETE': {
        key: 40,
        value: 'Kész',
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
        value: 'Függőben',
        label: 'bg-secondary',
    },
    
    'PLACED': {
        key: 20,
        value: 'Kiküldve',
        label: 'bg-primary',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'Felfüggesztve',
        label: 'bg-warning',
    },
    
    'COMPLETE': {
        key: 30,
        value: 'Kész',
        label: 'bg-success',
    },
    
    'CANCELLED': {
        key: 40,
        value: 'Törölve',
        label: 'bg-danger',
    },
    
    'LOST': {
        key: 50,
        value: 'Elveszett',
        label: 'bg-warning',
    },
    
    'RETURNED': {
        key: 60,
        value: 'Visszaküldve',
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
        value: 'Függőben',
        label: 'bg-secondary',
    },
    
    'IN_PROGRESS': {
        key: 15,
        value: 'Folyamatban',
        label: 'bg-primary',
    },
    
    'SHIPPED': {
        key: 20,
        value: 'Kiszállítva',
        label: 'bg-success',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'Felfüggesztve',
        label: 'bg-warning',
    },
    
    'COMPLETE': {
        key: 30,
        value: 'Kész',
        label: 'bg-success',
    },
    
    'CANCELLED': {
        key: 40,
        value: 'Törölve',
        label: 'bg-danger',
    },
    
    'LOST': {
        key: 50,
        value: 'Elveszett',
        label: 'bg-warning',
    },
    
    'RETURNED': {
        key: 60,
        value: 'Visszaküldve',
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
        value: 'Függőben',
        label: 'bg-secondary',
    },
    
    'IN_PROGRESS': {
        key: 20,
        value: 'Folyamatban',
        label: 'bg-primary',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'Felfüggesztve',
        label: 'bg-warning',
    },
    
    'COMPLETE': {
        key: 30,
        value: 'Kész',
        label: 'bg-success',
    },
    
    'CANCELLED': {
        key: 40,
        value: 'Törölve',
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
        value: 'Függőben',
        label: 'bg-secondary',
    },
    
    'RETURN': {
        key: 20,
        value: 'Visszavétel',
        label: 'bg-success',
    },
    
    'REPAIR': {
        key: 30,
        value: 'Javítás',
        label: 'bg-primary',
    },
    
    'REPLACE': {
        key: 40,
        value: 'Csere',
        label: 'bg-warning',
    },
    
    'REFUND': {
        key: 50,
        value: 'Visszatérítés',
        label: 'bg-info',
    },
    
    'REJECT': {
        key: 60,
        value: 'Elutasított',
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

