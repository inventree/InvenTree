{% load i18n %}
{% load inventree_extras %}


// Create a new SalesOrder
function createSalesOrder(options={}) {

    constructForm('{% url "api-so-list" %}', {
        method: 'POST',
        fields: {
            reference: {
                prefix: '{% settings_value "SALESORDER_REFERENCE_PREFIX" %}',
            },
            customer: {
                value: options.customer,
            },
            description: {},
            target_date: {
                icon: 'fa-calendar-alt',
            },
            link: {
                icon: 'fa-link',
            },
            responsible: {
                icon: 'fa-user',
            }
        },
        onSuccess: function(data) {
            location.href = `/order/sales-order/${data.pk}/`;
        },
        title: '{% trans "Create Sales Order" %}',
    });
}

// Create a new PurchaseOrder
function createPurchaseOrder(options={}) {

    constructForm('{% url "api-po-list" %}', {
        method: 'POST',
        fields: {
            reference: {
                prefix: "{% settings_value 'PURCHASEORDER_REFERENCE_PREFIX' %}",   
            },
            supplier: {
                value: options.supplier,
            },
            description: {},
            target_date: {
                icon: 'fa-calendar-alt',
            },
            link: {
                icon: 'fa-link',
            },
            responsible: {
                icon: 'fa-user',
            }
        },
        onSuccess: function(data) {
            location.href = `/order/purchase-order/${data.pk}/`;
        },
        title: '{% trans "Create Purchase Order" %}',
    });
}


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

    var src = e.srcElement || e.target;

    var part = $(src).attr('part');

    console.log('part: ' + part);

    if (!part) {
        part = $(src).closest('button').attr('part');
        console.log('parent: ' + part);
    }

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

    var supplier = $(src).attr('supplierid');

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

    var filters = loadTableFilters("purchaseorder");

    for (var key in options.params) {
        filters[key] = options.params[key];
    }

    options.url = options.url || '{% url "api-po-list" %}';

    setupFilterList("purchaseorder", $(table));

    $(table).inventreeTable({
        url: options.url,
        queryParams: filters,
        name: 'purchaseorder',
        groupBy: false,
        sidePagination: 'server',
        original: options.params,
        formatNoMatches: function() { return '{% trans "No purchase orders found" %}'; },
        columns: [
            {
                title: '',
                visible: true,
                checkbox: true,
                switchable: false,
            },
            {
                field: 'reference',
                title: '{% trans "Purchase Order" %}',
                sortable: true,
                switchable: false,
                formatter: function(value, row, index, field) {

                    var prefix = "{% settings_value 'PURCHASEORDER_REFERENCE_PREFIX' %}";

                    if (prefix) {
                        value = `${prefix}${value}`;
                    }

                    var html = renderLink(value, `/order/purchase-order/${row.pk}/`);

                    if (row.overdue) {
                        html += makeIconBadge('fa-calendar-times icon-red', '{% trans "Order is overdue" %}');
                    }

                    return html;
                }
            },  
            {
                field: 'supplier_detail',
                title: '{% trans "Supplier" %}',
                sortable: true,
                sortName: 'supplier__name',
                formatter: function(value, row, index, field) {
                    return imageHoverIcon(row.supplier_detail.image) + renderLink(row.supplier_detail.name, `/company/${row.supplier}/purchase-orders/`);
                }
            },
            {
                field: 'supplier_reference',
                title: '{% trans "Supplier Reference" %}',
            },
            {
                field: 'description',
                title: '{% trans "Description" %}',
            },
            {
                field: 'status',
                title: '{% trans "Status" %}',
                sortable: true,
                formatter: function(value, row, index, field) {
                    return purchaseOrderStatusDisplay(row.status, row.status_text);
                }
            },
            {
                field: 'creation_date',
                title: '{% trans "Date" %}',
                sortable: true,
            },
            {
                field: 'target_date',
                title: '{% trans "Target Date" %}',
                sortable: true,
            },
            {
                field: 'line_items',
                title: '{% trans "Items" %}',
                sortable: true,
            },
        ],
    });
}

function loadSalesOrderTable(table, options) {

    options.params = options.params || {};
    options.params['customer_detail'] = true;

    var filters = loadTableFilters("salesorder");

    for (var key in options.params) {
        filters[key] = options.params[key];
    }

    options.url = options.url || '{% url "api-so-list" %}';

    setupFilterList("salesorder", $(table));

    $(table).inventreeTable({
        url: options.url,
        queryParams: filters,
        name: 'salesorder',
        groupBy: false,
        sidePagination: 'server',
        original: options.params,
        formatNoMatches: function() { return '{% trans "No sales orders found" %}'; },
        columns: [
            {
                title: '',
                checkbox: true,
                visible: true,
                switchable: false,
            },
            {
                sortable: true,
                field: 'reference',
                title: '{% trans "Sales Order" %}',
                formatter: function(value, row, index, field) {

                    var prefix = "{% settings_value 'SALESORDER_REFERENCE_PREFIX' %}";

                    if (prefix) {
                        value = `${prefix}${value}`;
                    }

                    var html = renderLink(value, `/order/sales-order/${row.pk}/`);

                    if (row.overdue) {
                        html += makeIconBadge('fa-calendar-times icon-red', '{% trans "Order is overdue" %}');
                    }

                    return html;
                },
            },
            {
                sortable: true,
                sortName: 'customer__name',
                field: 'customer_detail',
                title: '{% trans "Customer" %}',
                formatter: function(value, row, index, field) {

                    if (!row.customer_detail) {
                        return '{% trans "Invalid Customer" %}';
                    }

                    return imageHoverIcon(row.customer_detail.image) + renderLink(row.customer_detail.name, `/company/${row.customer}/sales-orders/`);
                }
            },
            {
                sortable: true,
                field: 'customer_reference',
                title: '{% trans "Customer Reference" %}',
            },
            {
                sortable: false,
                field: 'description',
                title: '{% trans "Description" %}',
            },
            {
                sortable: true,
                field: 'status',
                title: '{% trans "Status" %}',
                formatter: function(value, row, index, field) {
                    return salesOrderStatusDisplay(row.status, row.status_text);
                }
            },
            {
                sortable: true,
                field: 'creation_date',
                title: '{% trans "Creation Date" %}',
            },
            {
                sortable: true,
                field: 'target_date',
                title: '{% trans "Target Date" %}',
            },
            {
                sortable: true,
                field: 'shipment_date',
                title: '{% trans "Shipment Date" %}',
            },
            {
                sortable: true,
                field: 'line_items',
                title: '{% trans "Items" %}'
            },
        ],
    });
}


function loadSalesOrderAllocationTable(table, options={}) {
    /**
     * Load a table with SalesOrderAllocation items
     */

    options.params = options.params || {};

    options.params['location_detail'] = true;
    options.params['part_detail'] = true;
    options.params['item_detail'] = true;
    options.params['order_detail'] = true;

    var filters = loadTableFilters("salesorderallocation");

    for (var key in options.params) {
        filters[key] = options.params[key];
    }

    setupFilterList("salesorderallocation", $(table));

    $(table).inventreeTable({
        url: '{% url "api-so-allocation-list" %}',
        queryParams: filters,
        name: 'salesorderallocation',
        groupBy: false,
        search: false,
        paginationVAlign: 'bottom',
        original: options.params,
        formatNoMatches: function() { return '{% trans "No sales order allocations found" %}'; },
        columns: [
            {
                field: 'pk',
                visible: false,
                switchable: false,
            },
            {
                field: 'order',
                switchable: false,
                title: '{% trans "Order" %}',
                switchable: false,
                formatter: function(value, row) {

                    var prefix = "{% settings_value 'SALESORDER_REFERENCE_PREFIX' %}";

                    var ref = `${prefix}${row.order_detail.reference}`;

                    return renderLink(ref, `/order/sales-order/${row.order}/`);
                }
            },
            {
                field: 'item',
                title: '{% trans "Stock Item" %}',
                formatter: function(value, row) {
                    // Render a link to the particular stock item

                    var link = `/stock/item/${row.item}/`;
                    var text = `{% trans "Stock Item" %} ${row.item}`;

                    return renderLink(text, link);
                }
            },
            {
                field: 'location',
                title: '{% trans "Location" %}',
                formatter: function(value, row) {

                    if (!value) {
                        return '{% trans "Location not specified" %}';
                    }
                    
                    var link = `/stock/location/${value}`;
                    var text = row.location_detail.description;

                    return renderLink(text, link);
                }
            },
            {
                field: 'quantity',
                title: '{% trans "Quantity" %}',
                sortable: true,
            }
        ]
    });
}