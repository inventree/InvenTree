function removeOrderRowFromOrderWizard(e) {
    /* Remove a part selection from an order form. */

    e = e || window.event;

    var src = e.target || e.srcElement;

    var row = $(src).attr('row');

    $('#' + row).remove();
}

function newSupplierPartFromOrderWizard(e) {
    /* Create a new supplier part directly from an order form.
     * Launches a secondary modal and (if successful),
     * back-populates the selected row.
     */

    e = e || window.event;

    var src = e.target || e.srcElement;

    var part = $(src).attr('part-id');

    launchModalForm("/supplier-part/new/", {
        modal: '#modal-form-secondary',
        data: {
            part: part,
        },
        success: function(response) {
            /* A new supplier part has been created! */

            var dropdown = '#id_supplier_part_' + part;

            var option = new Option(response.text, response.pk, true, true);

            $('#modal-form').find(dropdown).append(option).trigger('change');
        },
    });
}

function newPurchaseOrderFromOrderWizard(e) {
    /* Create a new purchase order directly from an order form.
     * Launches a secondary modal and (if successful),
     * back-fills the newly created purchase order.
     */

    e = e || window.event;

    var src = e.target || e.srcElement;

    var supplier = $(src).attr('supplier-id');

    launchModalForm("/order/purchase-order/new/", {
        modal: '#modal-form-secondary',
        data: {
            supplier: supplier,
        },
        success: function(response) {
            /* A new purchase order has been created! */

            var dropdown = '#id-purchase-order-' + supplier;

            var option = new Option(response.text, response.pk, true, true);

            $('#modal-form').find(dropdown).append(option).trigger('change');
        },
    });
}

function editPurchaseOrderLineItem(e) {

    /* Edit a purchase order line item in a modal form.
     */

    e = e || window.event;

    var src = e.target || e.srcElement;

    var url = $(src).attr('url');

    launchModalForm(url, {
        reload: true,
    });
}

function removePurchaseOrderLineItem(e) {

    /* Delete a purchase order line item in a modal form 
     */

    e = e || window.event;

    var src = e.target || e.srcElement;

    var url = $(src).attr('url');

    launchModalForm(url, {
        reload: true,
    });
}


function loadPurchaseOrderTable(table, options) {
    /* Create a purchase-order table */

    table.inventreeTable({
        url: options.url,
        formatNoMatches: function() { return "No purchase orders found"; },
        columns: [
            {
                field: 'pk',
                title: 'ID',
                visible: false,
            },
            {
                sortable: true,
                field: 'supplier',
                title: 'Supplier',
                formatter: function(value, row, index, field) {
                    return imageHoverIcon(row.supplier__image) + renderLink(row.supplier__name, '/company/' + value + '/purchase-orders/');
                }
            },
            {
                sortable: true,
                field: 'reference',
                title: 'Reference',
                formatter: function(value, row, index, field) {
                    return renderLink(value, "/order/purchase-order/" + row.pk + "/");
                }
            },  
            {
                sortable: true,
                field: 'creation_date',
                title: 'Date',
            },
            {
                sortable: true,
                field: 'description',
                title: 'Description',
            },
            {
                sortable: true,
                field: 'status',
                title: 'Status',
                formatter: function(value, row, index, field) {
                    return orderStatusLabel(row.status, row.status_text);
                }
            },
            {
                sortable: true,
                field: 'lines',
                title: 'Items'
            },
        ],
    });
}


function orderStatusLabel(code, label) {
    /* Render a purchase-order status label. */

    var html = "<span class='label";

    switch (code) {
    case 10:  // pending   
        html += " label-info";
        break;
    case  20:  // placed
        html += " label-primary";
        break;
    case 30:  // complete
        html += " label-success";
        break;
    case 40:  // cancelled
    case 50:  // lost
        html += " label-warning";
        break;
    case 60:  // returned
        html += " label-danger";
        break;
    default:
        break;
    }

    html += "'>";
    html += label;
    html += "</span>";

    console.log(html);

    return html;
}