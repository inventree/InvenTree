



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
        value: 'Necessita de atenção',
        label: 'bg-warning',
    },
    
    'DAMAGED': {
        key: 55,
        value: 'Danificado',
        label: 'bg-warning',
    },
    
    'DESTROYED': {
        key: 60,
        value: 'Destruído',
        label: 'bg-danger',
    },
    
    'REJECTED': {
        key: 65,
        value: 'Rejeitado',
        label: 'bg-danger',
    },
    
    'LOST': {
        key: 70,
        value: 'Perdido',
        label: 'bg-dark',
    },
    
    'QUARANTINED': {
        key: 75,
        value: 'Em quarentena',
        label: 'bg-info',
    },
    
    'RETURNED': {
        key: 85,
        value: 'Retornado',
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
        value: 'Entrada de rastreamento de estoque antiga',
        label: 'bg-secondary',
    },
    
    'CREATED': {
        key: 1,
        value: 'Item de estoque criado',
        label: 'bg-secondary',
    },
    
    'EDITED': {
        key: 5,
        value: 'Item de estoque editado',
        label: 'bg-secondary',
    },
    
    'ASSIGNED_SERIAL': {
        key: 6,
        value: 'Número de série atribuído',
        label: 'bg-secondary',
    },
    
    'STOCK_COUNT': {
        key: 10,
        value: 'Estoque contado',
        label: 'bg-secondary',
    },
    
    'STOCK_ADD': {
        key: 11,
        value: 'Estoque adicionado manualmente',
        label: 'bg-secondary',
    },
    
    'STOCK_REMOVE': {
        key: 12,
        value: 'Estoque removido manualmente',
        label: 'bg-secondary',
    },
    
    'STOCK_MOVE': {
        key: 20,
        value: 'Local alterado',
        label: 'bg-secondary',
    },
    
    'STOCK_UPDATE': {
        key: 25,
        value: 'Estoque atualizado',
        label: 'bg-secondary',
    },
    
    'INSTALLED_INTO_ASSEMBLY': {
        key: 30,
        value: 'Instalado na montagem',
        label: 'bg-secondary',
    },
    
    'REMOVED_FROM_ASSEMBLY': {
        key: 31,
        value: 'Removido da montagem',
        label: 'bg-secondary',
    },
    
    'INSTALLED_CHILD_ITEM': {
        key: 35,
        value: 'Instalado componente do Item',
        label: 'bg-secondary',
    },
    
    'REMOVED_CHILD_ITEM': {
        key: 36,
        value: 'Removido componente do Item',
        label: 'bg-secondary',
    },
    
    'SPLIT_FROM_PARENT': {
        key: 40,
        value: 'Separado do Item Paternal',
        label: 'bg-secondary',
    },
    
    'SPLIT_CHILD_ITEM': {
        key: 42,
        value: 'Separar o Item filho',
        label: 'bg-secondary',
    },
    
    'MERGED_STOCK_ITEMS': {
        key: 45,
        value: 'Itens de estoque mesclados',
        label: 'bg-secondary',
    },
    
    'CONVERTED_TO_VARIANT': {
        key: 48,
        value: 'Convertido para variável',
        label: 'bg-secondary',
    },
    
    'BUILD_OUTPUT_CREATED': {
        key: 50,
        value: 'Criação dos pedidos de produção criado',
        label: 'bg-secondary',
    },
    
    'BUILD_OUTPUT_COMPLETED': {
        key: 55,
        value: 'Criação do pedido de produção completado',
        label: 'bg-secondary',
    },
    
    'BUILD_OUTPUT_REJECTED': {
        key: 56,
        value: 'Saída do pedido de produção rejeitada',
        label: 'bg-secondary',
    },
    
    'BUILD_CONSUMED': {
        key: 57,
        value: 'Usado no pedido de produção',
        label: 'bg-secondary',
    },
    
    'SHIPPED_AGAINST_SALES_ORDER': {
        key: 60,
        value: 'Enviado contra o Pedido de Venda',
        label: 'bg-secondary',
    },
    
    'RECEIVED_AGAINST_PURCHASE_ORDER': {
        key: 70,
        value: 'Recebido referente ao Pedido de Compra',
        label: 'bg-secondary',
    },
    
    'RETURNED_AGAINST_RETURN_ORDER': {
        key: 80,
        value: 'Devolvido contra Pedido de Retorno',
        label: 'bg-secondary',
    },
    
    'SENT_TO_CUSTOMER': {
        key: 100,
        value: 'Enviado ao cliente',
        label: 'bg-secondary',
    },
    
    'RETURNED_FROM_CUSTOMER': {
        key: 105,
        value: 'Devolvido pelo cliente',
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
        value: 'Pendente',
        label: 'bg-secondary',
    },
    
    'PRODUCTION': {
        key: 20,
        value: 'Produção',
        label: 'bg-primary',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'On Hold',
        label: 'bg-warning',
    },
    
    'CANCELLED': {
        key: 30,
        value: 'Cancelado',
        label: 'bg-danger',
    },
    
    'COMPLETE': {
        key: 40,
        value: 'Completado',
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
        value: 'Pendente',
        label: 'bg-secondary',
    },
    
    'PLACED': {
        key: 20,
        value: 'Colocado',
        label: 'bg-primary',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'On Hold',
        label: 'bg-warning',
    },
    
    'COMPLETE': {
        key: 30,
        value: 'Completado',
        label: 'bg-success',
    },
    
    'CANCELLED': {
        key: 40,
        value: 'Cancelado',
        label: 'bg-danger',
    },
    
    'LOST': {
        key: 50,
        value: 'Perdido',
        label: 'bg-warning',
    },
    
    'RETURNED': {
        key: 60,
        value: 'Retornado',
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
        value: 'Pendente',
        label: 'bg-secondary',
    },
    
    'IN_PROGRESS': {
        key: 15,
        value: 'Em Progresso',
        label: 'bg-primary',
    },
    
    'SHIPPED': {
        key: 20,
        value: 'Enviado',
        label: 'bg-success',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'On Hold',
        label: 'bg-warning',
    },
    
    'COMPLETE': {
        key: 30,
        value: 'Completado',
        label: 'bg-success',
    },
    
    'CANCELLED': {
        key: 40,
        value: 'Cancelado',
        label: 'bg-danger',
    },
    
    'LOST': {
        key: 50,
        value: 'Perdido',
        label: 'bg-warning',
    },
    
    'RETURNED': {
        key: 60,
        value: 'Retornado',
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
        value: 'Pendente',
        label: 'bg-secondary',
    },
    
    'IN_PROGRESS': {
        key: 20,
        value: 'Em Progresso',
        label: 'bg-primary',
    },
    
    'ON_HOLD': {
        key: 25,
        value: 'On Hold',
        label: 'bg-warning',
    },
    
    'COMPLETE': {
        key: 30,
        value: 'Completado',
        label: 'bg-success',
    },
    
    'CANCELLED': {
        key: 40,
        value: 'Cancelado',
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
        value: 'Pendente',
        label: 'bg-secondary',
    },
    
    'RETURN': {
        key: 20,
        value: 'Devolução',
        label: 'bg-success',
    },
    
    'REPAIR': {
        key: 30,
        value: 'Consertar',
        label: 'bg-primary',
    },
    
    'REPLACE': {
        key: 40,
        value: 'Substituir',
        label: 'bg-warning',
    },
    
    'REFUND': {
        key: 50,
        value: 'Reembolsar',
        label: 'bg-info',
    },
    
    'REJECT': {
        key: 60,
        value: 'Recusar',
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

