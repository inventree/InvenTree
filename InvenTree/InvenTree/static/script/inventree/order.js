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

    options.params = options.params || {};

    options.params['supplier_detail'] = true;

    var filters = loadTableFilters("order");

    for (var key in options.params) {
        filters[key] = options.params[key];
    }

    setupFilterList("order", $(table));

    $(table).inventreeTable({
        url: options.url,
        queryParams: filters,
        groupBy: false,
        original: options.params,
        formatNoMatches: function() { return "No purchase orders found"; },
        columns: [
            {
                field: 'pk',
                title: 'ID',
                visible: false,
            },
            {
                sortable: true,
                field: 'reference',
                title: 'Purchase Order',
                formatter: function(value, row, index, field) {
                    return renderLink(value, `/order/purchase-order/${row.pk}/`);
                }
            },  
            {
                sortable: true,
                field: 'supplier_detail',
                title: 'Supplier',
                formatter: function(value, row, index, field) {
                    return imageHoverIcon(row.supplier_detail.image) + renderLink(row.supplier_detail.name, `/company/${row.supplier}/purchase-orders/`);
                }
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
                    return orderStatusDisplay(row.status, row.status_text);
                }
            },
            {
                sortable: true,
                field: 'creation_date',
                title: 'Date',
            },
            {
                sortable: true,
                field: 'line_items',
                title: 'Items'
            },
        ],
    });
}

function loadSalesOrderTable(table, options) {

    options.params = options.params || {};
    options.params['customer_detail'] = true;

    var filters = loadTableFilters("table");

    for (var key in options.params) {
        filters[key] = options.params[key];
    }

    setupFilterList("order", $(table));

    $(table).inventreeTable({
        url: options.url,
        queryParams: filters,
        groupBy: false,
        original: options.params,
        formatNoMatches: function() { return "No sales orders found"; },
        columns: [
            {
                field: 'pk',
                title: 'ID',
                visible: false,
            },
            {
                sortable: true,
                field: 'reference',
                title: 'Sales Order',
                formatter: function(value, row, index, field) {
                    return renderLink(value, `/order/sales-order/${row.pk}/`);
                },
            },
            {
                sortable: true,
                field: 'customer_detail',
                title: 'Customer',
                formatter: function(value, row, index, field) {
                    return imageHoverIcon(row.customer_detail.image) + renderLink(row.customer_detail.name, `/company/${row.customer}/sales-orders/`);
                }
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
                    return orderStatusDisplay(row.status, row.status_text);
                }
            },
            {
                sortable: true,
                field: 'creation_date',
                title: 'Date',
            },
            {
                sortable: true,
                field: 'line_items',
                title: 'Items'
            },
        ],
    });
}
