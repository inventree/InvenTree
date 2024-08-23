



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
        value: 'ΟΚ',
        label: 'bg-success',
    },
    
    'ATTENTION': {
        key: 50,
        value: 'Απαιτείται προσοχή',
        label: 'bg-warning',
    },
    
    'DAMAGED': {
        key: 55,
        value: 'Κατεστραμμένο',
        label: 'bg-warning',
    },
    
    'DESTROYED': {
        key: 60,
        value: 'Καταστράφηκε',
        label: 'bg-danger',
    },
    
    'REJECTED': {
        key: 65,
        value: 'Απορρίφθηκε',
        label: 'bg-danger',
    },
    
    'LOST': {
        key: 70,
        value: 'Χάθηκε',
        label: 'bg-dark',
    },
    
    'QUARANTINED': {
        key: 75,
        value: 'Σε Καραντίνα',
        label: 'bg-info',
    },
    
    'RETURNED': {
        key: 85,
        value: 'Επιστράφηκε',
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
        value: 'Καταχώρηση παλαιού αποθέματος',
        label: 'bg-secondary',
    },
    
    'CREATED': {
        key: 1,
        value: 'Το αντικείμενο αποθεμάτων δημιουργήθηκε',
        label: 'bg-secondary',
    },
    
    'EDITED': {
        key: 5,
        value: 'Έγινε συγχώνευση αποθεμάτων',
        label: 'bg-secondary',
    },
    
    'ASSIGNED_SERIAL': {
        key: 6,
        value: 'Εκχωρημένος σειριακός κωδικός',
        label: 'bg-secondary',
    },
    
    'STOCK_COUNT': {
        key: 10,
        value: 'Απόθεμα που μετρήθηκε',
        label: 'bg-secondary',
    },
    
    'STOCK_ADD': {
        key: 11,
        value: 'Προστέθηκε απόθεμα χειροκίνητα',
        label: 'bg-secondary',
    },
    
    'STOCK_REMOVE': {
        key: 12,
        value: 'Αφαιρέθηκε απόθεμα χειροκίνητα',
        label: 'bg-secondary',
    },
    
    'STOCK_MOVE': {
        key: 20,
        value: 'Η τοποθεσία τροποποιήθηκε',
        label: 'bg-secondary',
    },
    
    'STOCK_UPDATE': {
        key: 25,
        value: 'Το απόθεμα ενημερώθηκε',
        label: 'bg-secondary',
    },
    
    'INSTALLED_INTO_ASSEMBLY': {
        key: 30,
        value: 'Εγκαταστάθηκε στη συναρμολόγηση',
        label: 'bg-secondary',
    },
    
    'REMOVED_FROM_ASSEMBLY': {
        key: 31,
        value: 'Αφαιρέθηκε από τη συναρμολόγηση',
        label: 'bg-secondary',
    },
    
    'INSTALLED_CHILD_ITEM': {
        key: 35,
        value: 'Εγκαταστάθηκε αντικείμενο',
        label: 'bg-secondary',
    },
    
    'REMOVED_CHILD_ITEM': {
        key: 36,
        value: 'Αφαιρέθηκε αντικείμενο',
        label: 'bg-secondary',
    },
    
    'SPLIT_FROM_PARENT': {
        key: 40,
        value: 'Έγινε διαχωρισμός από το γονεϊκό αρχείο',
        label: 'bg-secondary',
    },
    
    'SPLIT_CHILD_ITEM': {
        key: 42,
        value: 'Διαχωρίστηκε θυγατρικό στοιχείο',
        label: 'bg-secondary',
    },
    
    'MERGED_STOCK_ITEMS': {
        key: 45,
        value: 'Έγινε συγχώνευση αποθεμάτων',
        label: 'bg-secondary',
    },
    
    'CONVERTED_TO_VARIANT': {
        key: 48,
        value: 'Μετατράπηκε σε παραλλαγή',
        label: 'bg-secondary',
    },
    
    'BUILD_OUTPUT_CREATED': {
        key: 50,
        value: 'Δημιουργήθηκε η έξοδος παραγγελίας',
        label: 'bg-secondary',
    },
    
    'BUILD_OUTPUT_COMPLETED': {
        key: 55,
        value: 'Η έξοδος της σειράς κατασκευής ολοκληρώθηκε',
        label: 'bg-secondary',
    },
    
    'BUILD_OUTPUT_REJECTED': {
        key: 56,
        value: 'Η εντολή κατασκευής απορρίφθηκε',
        label: 'bg-secondary',
    },
    
    'BUILD_CONSUMED': {
        key: 57,
        value: 'Κατανάλωση με εντολή κατασκευής',
        label: 'bg-secondary',
    },
    
    'SHIPPED_AGAINST_SALES_ORDER': {
        key: 60,
        value: 'Αποστολή έναντι Εντολής Πώλησης',
        label: 'bg-secondary',
    },
    
    'RECEIVED_AGAINST_PURCHASE_ORDER': {
        key: 70,
        value: 'Λήφθηκε έναντι Εντολής Αγοράς',
        label: 'bg-secondary',
    },
    
    'RETURNED_AGAINST_RETURN_ORDER': {
        key: 80,
        value: 'Επιστράφηκε έναντι Εντολής Αγοράς',
        label: 'bg-secondary',
    },
    
    'SENT_TO_CUSTOMER': {
        key: 100,
        value: 'Απεστάλη στον πελάτη',
        label: 'bg-secondary',
    },
    
    'RETURNED_FROM_CUSTOMER': {
        key: 105,
        value: 'Επιστράφηκε από πελάτη',
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
        value: 'Σε εκκρεμότητα',
        label: 'bg-secondary',
    },
    
    'PRODUCTION': {
        key: 20,
        value: 'Παραγωγή',
        label: 'bg-primary',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'On Hold',
        label: 'bg-warning',
    },
    
    'CANCELLED': {
        key: 30,
        value: 'Ακυρώθηκε',
        label: 'bg-danger',
    },
    
    'COMPLETE': {
        key: 40,
        value: 'Ολοκληρώθηκε',
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
        value: 'Σε εκκρεμότητα',
        label: 'bg-secondary',
    },
    
    'PLACED': {
        key: 20,
        value: 'Τοποθετήθηκε',
        label: 'bg-primary',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'On Hold',
        label: 'bg-warning',
    },
    
    'COMPLETE': {
        key: 30,
        value: 'Ολοκληρώθηκε',
        label: 'bg-success',
    },
    
    'CANCELLED': {
        key: 40,
        value: 'Ακυρώθηκε',
        label: 'bg-danger',
    },
    
    'LOST': {
        key: 50,
        value: 'Χάθηκε',
        label: 'bg-warning',
    },
    
    'RETURNED': {
        key: 60,
        value: 'Επιστράφηκε',
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
        value: 'Σε εκκρεμότητα',
        label: 'bg-secondary',
    },
    
    'IN_PROGRESS': {
        key: 15,
        value: 'Σε Εξέλιξη',
        label: 'bg-primary',
    },
    
    'SHIPPED': {
        key: 20,
        value: 'Αποστάλθηκε',
        label: 'bg-success',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'On Hold',
        label: 'bg-warning',
    },
    
    'COMPLETE': {
        key: 30,
        value: 'Ολοκληρώθηκε',
        label: 'bg-success',
    },
    
    'CANCELLED': {
        key: 40,
        value: 'Ακυρώθηκε',
        label: 'bg-danger',
    },
    
    'LOST': {
        key: 50,
        value: 'Χάθηκε',
        label: 'bg-warning',
    },
    
    'RETURNED': {
        key: 60,
        value: 'Επιστράφηκε',
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
        value: 'Σε εκκρεμότητα',
        label: 'bg-secondary',
    },
    
    'IN_PROGRESS': {
        key: 20,
        value: 'Σε Εξέλιξη',
        label: 'bg-primary',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'On Hold',
        label: 'bg-warning',
    },
    
    'COMPLETE': {
        key: 30,
        value: 'Ολοκληρώθηκε',
        label: 'bg-success',
    },
    
    'CANCELLED': {
        key: 40,
        value: 'Ακυρώθηκε',
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
        value: 'Σε εκκρεμότητα',
        label: 'bg-secondary',
    },
    
    'RETURN': {
        key: 20,
        value: 'Επιστροφή',
        label: 'bg-success',
    },
    
    'REPAIR': {
        key: 30,
        value: 'Επισκευή',
        label: 'bg-primary',
    },
    
    'REPLACE': {
        key: 40,
        value: 'Αντικατάσταση',
        label: 'bg-warning',
    },
    
    'REFUND': {
        key: 50,
        value: 'Επιστροφή χρημάτων',
        label: 'bg-info',
    },
    
    'REJECT': {
        key: 60,
        value: 'Απόρριψη',
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

