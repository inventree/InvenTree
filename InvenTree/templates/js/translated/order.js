{% load i18n %}
{% load inventree_extras %}

/* globals
    companyFormFields,
    constructForm,
    createSupplierPart,
    global_settings,
    imageHoverIcon,
    inventreeGet,
    launchModalForm,
    loadTableFilters,
    makeIconBadge,
    purchaseOrderStatusDisplay,
    receivePurchaseOrderItems,
    renderLink,
    salesOrderStatusDisplay,
    setupFilterList,
*/

/* exported
    createSalesOrder,
    editPurchaseOrderLineItem,
    exportOrder,
    loadPurchaseOrderLineItemTable,
    loadPurchaseOrderTable,
    loadSalesOrderAllocationTable,
    loadSalesOrderLineItemTable,
    loadSalesOrderTable,
    newPurchaseOrderFromOrderWizard,
    newSupplierPartFromOrderWizard,
    removeOrderRowFromOrderWizard,
    removePurchaseOrderLineItem,
*/

// Create a new SalesOrder
function createSalesOrder(options={}) {

    constructForm('{% url "api-so-list" %}', {
        method: 'POST',
        fields: {
            reference: {
                prefix: global_settings.SALESORDER_REFERENCE_PREFIX,
            },
            customer: {
                value: options.customer,
                secondary: {
                    title: '{% trans "Add Customer" %}',
                    fields: function() {
                        var fields = companyFormFields();
                        
                        fields.is_customer.value = true;

                        return fields;
                    }
                }
            },
            customer_reference: {},
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
                prefix: global_settings.PURCHASEORDER_REFERENCE_PREFIX,
            },
            supplier: {
                icon: 'fa-building',
                value: options.supplier,
                secondary: {
                    title: '{% trans "Add Supplier" %}',
                    fields: function() {
                        var fields = companyFormFields();

                        fields.is_supplier.value = true;

                        return fields;
                    }
                }
            },
            supplier_reference: {},
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

            if (options.onSuccess) {
                options.onSuccess(data);
            } else {
                // Default action is to redirect browser to the new PO
                location.href = `/order/purchase-order/${data.pk}/`;
            }
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

    if (!part) {
        part = $(src).closest('button').attr('part');
    }

    createSupplierPart({
        part: part,
        onSuccess: function(data) {
                        
            // TODO: 2021-08-23 - This whole form wizard needs to be refactored.
            // In the future, use the API forms functionality to add the new item
            // For now, this hack will have to do...

            var dropdown = `#id_supplier_part_${part}`;

            var pk = data.pk;

            inventreeGet(
                `/api/company/part/${pk}/`,
                {
                    supplier_detail: true,
                },
                {
                    success: function(response) {
                        var text = '';

                        if (response.supplier_detail) {
                            text += response.supplier_detail.name;
                            text += ' | ';
                        }

                        text += response.SKU;

                        var option = new Option(text, pk, true, true);

                        $('#modal-form').find(dropdown).append(option).trigger('change');
                    }
                }
            );
        }
    });
}

/**
 * Export an order (PurchaseOrder or SalesOrder)
 * 
 * - Display a simple form which presents the user with export options
 * 
 */
function exportOrder(redirect_url, options={}) {

    var format = options.format;

    // If default format is not provided, lookup
    if (!format) {
        format = inventreeLoad('order-export-format', 'csv');
    }

    constructFormBody({}, {
        title: '{% trans "Export Order" %}',
        fields: {
            format: {
                label: '{% trans "Format" %}',
                help_text: '{% trans "Select file format" %}',
                required: true,
                type: 'choice',
                value: format,
                choices: exportFormatOptions(),
            }
        },
        onSubmit: function(fields, opts) {

            var format = getFormFieldValue('format', fields['format'], opts);

            // Save the format for next time
            inventreeSave('order-export-format', format);

            // Hide the modal
            $(opts.modal).modal('hide');

            // Download the file!
            location.href = `${redirect_url}?format=${format}`;
        }
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

    createPurchaseOrder({
        supplier: supplier,
        onSuccess: function(data) {

            // TODO: 2021-08-23 - The whole form wizard needs to be refactored
            // In the future, the drop-down should be using a dynamic AJAX request
            // to fill out the select2 options!

            var pk = data.pk;

            inventreeGet(
                `/api/order/po/${pk}/`,
                {
                    supplier_detail: true,
                },
                {
                    success: function(response) {
                        var text = global_settings.PURCHASEORDER_REFERENCE_PREFIX || '';

                        text += response.reference;

                        if (response.supplier_detail) {
                            text += ` ${response.supplier_detail.name}`;
                        }

                        var dropdown = `#id-purchase-order-${supplier}`;

                        var option = new Option(text, pk, true, true);
            
                        $('#modal-form').find(dropdown).append(option).trigger('change');
                    }
                }
            );
        }
    }); 
}


/**
 * Receive stock items against a PurchaseOrder
 * Uses the POReceive API endpoint
 * 
 * arguments:
 * - order_id, ID / PK for the PurchaseOrder instance
 * - line_items: A list of PurchaseOrderLineItems objects to be allocated
 * 
 * options:
 *  - 
 */
function receivePurchaseOrderItems(order_id, line_items, options={}) {

    if (line_items.length == 0) {
        showAlertDialog(
            '{% trans "Select Line Items" %}',
            '{% trans "At least one line item must be selected" %}',
        );
        return;
    }

    function renderLineItem(line_item, opts={}) {

        var pk = line_item.pk;

        // Part thumbnail + description
        var thumb = thumbnailImage(line_item.part_detail.thumbnail);

        var quantity = (line_item.quantity || 0) - (line_item.received || 0);
        
        if (quantity < 0) {
            quantity = 0;
        }

        // Quantity to Receive
        var quantity_input = constructField(
            `items_quantity_${pk}`,
            {
                type: 'decimal',
                min_value: 0,
                value: quantity,
                title: '{% trans "Quantity to receive" %}',
                required: true,
            },
            {
                hideLabels: true,
            }
        );

        // Construct list of StockItem status codes
        var choices = [];

        for (var key in stockCodes) {
            choices.push({
                value: key,
                display_name: stockCodes[key].value,
            });
        }

        var destination_input = constructField(
            `items_location_${pk}`,
            {
                type: 'related field',
                label: '{% trans "Location" %}',
                required: false,
            },
            {
                hideLabels: true,
            }
        );

        var status_input = constructField(
            `items_status_${pk}`,
            {
                type: 'choice',
                label: '{% trans "Stock Status" %}',
                required: true,
                choices: choices,
                value: 10, // OK
            },
            {
                hideLabels: true,
            }
        );

        // Button to remove the row
        var delete_button = `<div class='btn-group float-right' role='group'>`;

        delete_button += makeIconButton(
            'fa-times icon-red',
            'button-row-remove',
            pk,
            '{% trans "Remove row" %}',
        );

        delete_button += '</div>';

        var html = `
        <tr id='receive_row_${pk}' class='stock-receive-row'>
            <td id='part_${pk}'>
                ${thumb} ${line_item.part_detail.full_name}
            </td>
            <td id='sku_${pk}'>
                ${line_item.supplier_part_detail.SKU}
            </td>
            <td id='on_order_${pk}'>
                ${line_item.quantity}
            </td>
            <td id='received_${pk}'>
                ${line_item.received}
            </td>
            <td id='quantity_${pk}'>
                ${quantity_input}
            </td>
            <td id='status_${pk}'>
                ${status_input}
            </td>
            <td id='desination_${pk}'>
                ${destination_input}
            </td>
            <td id='actions_${pk}'>
                ${delete_button}
            </td>
        </tr>`;

        return html;
    }

    var table_entries = '';

    line_items.forEach(function(item) {
        table_entries += renderLineItem(item);
    });

    var html = ``;

    // Add table
    html += `
    <table class='table table-striped table-condensed' id='order-receive-table'>
        <thead>
            <tr>
                <th>{% trans "Part" %}</th>
                <th>{% trans "Order Code" %}</th>
                <th>{% trans "Ordered" %}</th>
                <th>{% trans "Received" %}</th>
                <th style='min-width: 50px;'>{% trans "Receive" %}</th>
                <th style='min-width: 150px;'>{% trans "Status" %}</th>
                <th style='min-width: 300px;'>{% trans "Destination" %}</th>
                <th></th>
            </tr>
        </thead>
        <tbody>
            ${table_entries}
        </tbody>
    </table>
    `;

    constructForm(`/api/order/po/${order_id}/receive/`, {
        method: 'POST',
        fields: {
            location: {},
        },
        preFormContent: html,
        confirm: true,
        confirmMessage: '{% trans "Confirm receipt of items" %}',
        title: '{% trans "Receive Purchase Order Items" %}',
        afterRender: function(fields, opts) {
            // Initialize the "destination" field for each item
            line_items.forEach(function(item) {

                var pk = item.pk;

                var name = `items_location_${pk}`;

                var field_details = {
                    name: name,
                    api_url: '{% url "api-location-list" %}',
                    filters: {

                    },
                    type: 'related field',
                    model: 'stocklocation',
                    required: false,
                    auto_fill: false,
                    value: item.destination || item.part_detail.default_location,
                    render_description: false,
                };

                initializeRelatedField(
                    field_details,
                    null,
                    opts,
                );

                addClearCallback(
                    name,
                    field_details,
                    opts
                );

                initializeChoiceField(
                    {
                        name: `items_status_${pk}`,
                    },
                    null,
                    opts
                );
            });

            // Add callbacks to remove rows
            $(opts.modal).find('.button-row-remove').click(function() {
                var pk = $(this).attr('pk');

                $(opts.modal).find(`#receive_row_${pk}`).remove();
            });
        },
        onSubmit: function(fields, opts) {
            // Extract data elements from the form
            var data = {
                items: [],
                location: getFormFieldValue('location', {}, opts),
            };

            var item_pk_values = [];

            line_items.forEach(function(item) {

                var pk = item.pk;

                var quantity = getFormFieldValue(`items_quantity_${pk}`, {}, opts);

                var status = getFormFieldValue(`items_status_${pk}`, {}, opts);

                var location = getFormFieldValue(`items_location_${pk}`, {}, opts);

                if (quantity != null) {
                    data.items.push({
                        line_item: pk,
                        quantity: quantity,
                        status: status,
                        location: location,
                    });

                    item_pk_values.push(pk);
                }

            });

            // Provide list of nested values
            opts.nested = {
                'items': item_pk_values,
            };

            inventreePut(
                opts.url,
                data,
                {
                    method: 'POST',
                    success: function(response) {
                        // Hide the modal
                        $(opts.modal).modal('hide');

                        if (options.success) {
                            options.success(response);
                        }
                    },
                    error: function(xhr) {
                        switch (xhr.status) {
                        case 400:
                            handleFormErrors(xhr.responseJSON, fields, opts);
                            break;
                        default:
                            $(opts.modal).modal('hide');
                            showApiError(xhr, opts.url);
                            break;
                        }
                    }
                }
            );
        }
    });
}


function editPurchaseOrderLineItem(e) {

    /* Edit a purchase order line item in a modal form.
     */

    e = e || window.event;

    var src = e.target || e.srcElement;

    var url = $(src).attr('url');

    // TODO: Migrate this to the API forms
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
    
    // TODO: Migrate this to the API forms
    launchModalForm(url, {
        reload: true,
    });
}


function loadPurchaseOrderTable(table, options) {
    /* Create a purchase-order table */

    options.params = options.params || {};

    options.params['supplier_detail'] = true;

    var filters = loadTableFilters('purchaseorder');

    for (var key in options.params) {
        filters[key] = options.params[key];
    }

    setupFilterList('purchaseorder', $(table));

    $(table).inventreeTable({
        url: '{% url "api-po-list" %}',
        queryParams: filters,
        name: 'purchaseorder',
        groupBy: false,
        sidePagination: 'server',
        original: options.params,
        formatNoMatches: function() {
            return '{% trans "No purchase orders found" %}';
        },
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
                formatter: function(value, row) {

                    var prefix = global_settings.PURCHASEORDER_REFERENCE_PREFIX;

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
                formatter: function(value, row) {
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
                formatter: function(value, row) {
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
            {
                field: 'responsible',
                title: '{% trans "Responsible" %}',
                switchable: true,
                sortable: false,
                formatter: function(value, row) {
                    var html = row.responsible_detail.name;

                    if (row.responsible_detail.label == 'group') {
                        html += `<span class='float-right fas fa-users'></span>`;
                    } else {
                        html += `<span class='float-right fas fa-user'></span>`;
                    }

                    return html;
                }
            },
        ],
    });
}


/**
 * Load a table displaying line items for a particular PurchasesOrder
 * @param {String} table - HTML ID tag e.g. '#table' 
 * @param {Object} options - options which must provide:
 *      - order (integer PK)
 *      - supplier (integer PK)
 *      - allow_edit (boolean)
 *      - allow_receive (boolean)
 */
function loadPurchaseOrderLineItemTable(table, options={}) {

    options.params = options.params || {};

    options.params['order'] = options.order;
    options.params['part_detail'] = true;

    var filters = loadTableFilters('purchaseorderlineitem');

    for (var key in options.params) {
        filters[key] = options.params[key];
    }
    
    var target = options.filter_target || '#filter-list-purchase-order-lines';

    setupFilterList('purchaseorderlineitem', $(table), target);

    function setupCallbacks() {
        if (options.allow_edit) {
            $(table).find('.button-line-edit').click(function() {
                var pk = $(this).attr('pk');

                constructForm(`/api/order/po-line/${pk}/`, {
                    fields: {
                        part: {
                            filters: {
                                part_detail: true,
                                supplier_detail: true,
                                supplier: options.supplier,
                            }
                        },
                        quantity: {},
                        reference: {},
                        purchase_price: {},
                        purchase_price_currency: {},
                        destination: {},
                        notes: {},
                    },
                    title: '{% trans "Edit Line Item" %}',
                    onSuccess: function() {
                        $(table).bootstrapTable('refresh');
                    }
                });
            });

            $(table).find('.button-line-delete').click(function() {
                var pk = $(this).attr('pk');

                constructForm(`/api/order/po-line/${pk}/`, {
                    method: 'DELETE',
                    title: '{% trans "Delete Line Item" %}',
                    onSuccess: function() {
                        $(table).bootstrapTable('refresh');
                    }
                });
            });
        }

        if (options.allow_receive) {
            $(table).find('.button-line-receive').click(function() {
                var pk = $(this).attr('pk');

                var line_item = $(table).bootstrapTable('getRowByUniqueId', pk);

                if (!line_item) {
                    console.log('WARNING: getRowByUniqueId returned null');
                    return;
                }

                receivePurchaseOrderItems(
                    options.order,
                    [
                        line_item,
                    ],
                    {
                        success: function() {
                            $(table).bootstrapTable('refresh');
                        }
                    }
                );
            });
        }
    }

    $(table).inventreeTable({
        onPostBody: setupCallbacks,
        name: 'purchaseorderlines',
        sidePagination: 'server',
        formatNoMatches: function() {
            return '{% trans "No line items found" %}';
        },
        queryParams: filters,
        original: options.params,
        url: '{% url "api-po-line-list" %}',
        showFooter: true,
        uniqueId: 'pk',
        columns: [
            {
                checkbox: true,
                visible: true,
                switchable: false,
            },
            {
                field: 'part',
                sortable: true,
                sortName: 'part_name',
                title: '{% trans "Part" %}',
                switchable: false,
                formatter: function(value, row, index, field) {
                    if (row.part) {
                        return imageHoverIcon(row.part_detail.thumbnail) + renderLink(row.part_detail.full_name, `/part/${row.part_detail.pk}/`);
                    } else { 
                        return '-';
                    }
                },
                footerFormatter: function() {
                    return '{% trans "Total" %}';
                }
            },
            {
                field: 'part_detail.description',
                title: '{% trans "Description" %}',
            },
            {
                sortable: true,
                sortName: 'SKU',
                field: 'supplier_part_detail.SKU',
                title: '{% trans "SKU" %}',
                formatter: function(value, row, index, field) {
                    if (value) {
                        return renderLink(value, `/supplier-part/${row.part}/`);
                    } else {
                        return '-';
                    }
                },
            },
            {
                sortable: true,
                sortName: 'MPN',
                field: 'supplier_part_detail.manufacturer_part_detail.MPN',
                title: '{% trans "MPN" %}',
                formatter: function(value, row, index, field) {
                    if (row.supplier_part_detail && row.supplier_part_detail.manufacturer_part) {
                        return renderLink(value, `/manufacturer-part/${row.supplier_part_detail.manufacturer_part}/`);
                    } else {
                        return '-';
                    }
                },
            },
            {
                sortable: true,
                field: 'reference',
                title: '{% trans "Reference" %}',
            },
            {
                sortable: true,
                switchable: false,
                field: 'quantity',
                title: '{% trans "Quantity" %}',
                footerFormatter: function(data) {
                    return data.map(function(row) {
                        return +row['quantity'];
                    }).reduce(function(sum, i) {
                        return sum + i;
                    }, 0);
                }
            },
            {
                sortable: true,
                field: 'purchase_price',
                title: '{% trans "Unit Price" %}',
                formatter: function(value, row) {
                    var formatter = new Intl.NumberFormat(
                        'en-US',
                        {
                            style: 'currency',
                            currency: row.purchase_price_currency
                        }
                    );
                    return formatter.format(row.purchase_price);
                }
            },
            {
                field: 'total_price',
                sortable: true,
                title: '{% trans "Total Price" %}',
                formatter: function(value, row) {
                    var formatter = new Intl.NumberFormat(
                        'en-US',
                        {
                            style: 'currency',
                            currency: row.purchase_price_currency
                        }
                    );
                    return formatter.format(row.purchase_price * row.quantity);
                },
                footerFormatter: function(data) {
                    var total = data.map(function(row) {
                        return +row['purchase_price']*row['quantity'];
                    }).reduce(function(sum, i) {
                        return sum + i;
                    }, 0);

                    var currency = (data.slice(-1)[0] && data.slice(-1)[0].purchase_price_currency) || 'USD';

                    var formatter = new Intl.NumberFormat(
                        'en-US',
                        {
                            style: 'currency',
                            currency: currency
                        }
                    );
                    
                    return formatter.format(total);
                }
            },
            {
                sortable: false,
                field: 'received',
                switchable: false,
                title: '{% trans "Received" %}',
                formatter: function(value, row, index, field) {
                    return makeProgressBar(row.received, row.quantity, {
                        id: `order-line-progress-${row.pk}`,
                    });
                },
                sorter: function(valA, valB, rowA, rowB) {
    
                    if (rowA.received == 0 && rowB.received == 0) {
                        return (rowA.quantity > rowB.quantity) ? 1 : -1;
                    }
    
                    var progressA = parseFloat(rowA.received) / rowA.quantity;
                    var progressB = parseFloat(rowB.received) / rowB.quantity;
    
                    return (progressA < progressB) ? 1 : -1;
                }
            },
            {
                field: 'destination',
                title: '{% trans "Destination" %}',
                formatter: function(value, row) {
                    if (value) {
                        return renderLink(row.destination_detail.pathstring, `/stock/location/${value}/`);
                    } else {
                        return '-';
                    }
                }
            },
            {
                field: 'notes',
                title: '{% trans "Notes" %}',
            },
            {
                switchable: false,
                field: 'buttons',
                title: '',
                formatter: function(value, row, index, field) {
                    var html = `<div class='btn-group'>`;
    
                    var pk = row.pk;
    
                    if (options.allow_edit) {
                        html += makeIconButton('fa-edit icon-blue', 'button-line-edit', pk, '{% trans "Edit line item" %}');
                        html += makeIconButton('fa-trash-alt icon-red', 'button-line-delete', pk, '{% trans "Delete line item" %}');
                    }

                    if (options.allow_receive && row.received < row.quantity) {
                        html += makeIconButton('fa-sign-in-alt', 'button-line-receive', pk, '{% trans "Receive line item" %}');
                    }
        
                    html += `</div>`;
    
                    return html;
                },
            }
        ]
    });

}


function loadSalesOrderTable(table, options) {

    options.params = options.params || {};
    options.params['customer_detail'] = true;

    var filters = loadTableFilters('salesorder');

    for (var key in options.params) {
        filters[key] = options.params[key];
    }

    options.url = options.url || '{% url "api-so-list" %}';

    setupFilterList('salesorder', $(table));

    $(table).inventreeTable({
        url: options.url,
        queryParams: filters,
        name: 'salesorder',
        groupBy: false,
        sidePagination: 'server',
        original: options.params,
        formatNoMatches: function() {
            return '{% trans "No sales orders found" %}';
        },
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
                formatter: function(value, row) {

                    var prefix = global_settings.SALESORDER_REFERENCE_PREFIX;

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
                formatter: function(value, row) {

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
                formatter: function(value, row) {
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

    var filters = loadTableFilters('salesorderallocation');

    for (var key in options.params) {
        filters[key] = options.params[key];
    }

    setupFilterList('salesorderallocation', $(table));

    $(table).inventreeTable({
        url: '{% url "api-so-allocation-list" %}',
        queryParams: filters,
        name: 'salesorderallocation',
        groupBy: false,
        search: false,
        paginationVAlign: 'bottom',
        original: options.params,
        formatNoMatches: function() {
            return '{% trans "No sales order allocations found" %}';
        },
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
                formatter: function(value, row) {

                    var prefix = global_settings.SALESORDER_REFERENCE_PREFIX;

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


/**
 * Display an "allocations" sub table, showing stock items allocated againt a sales order
 * @param {*} index 
 * @param {*} row 
 * @param {*} element 
 */
function showAllocationSubTable(index, row, element, options) {
    
    // Construct a sub-table element
    var html = `
    <div class='sub-table'>
        <table class='table table-striped table-condensed' id='allocation-table-${row.pk}'>
        </table>
    </div>`;

    element.html(html);

    var table = $(`#allocation-table-${row.pk}`);

    // Is the parent SalesOrder pending?
    var pending = options.status == {{ SalesOrderStatus.PENDING }};

    function setupCallbacks() {
        // Add callbacks for 'edit' buttons
        table.find('.button-allocation-edit').click(function() {

            var pk = $(this).attr('pk');

            // Edit the sales order alloction
            constructForm(
                `/api/order/so-allocation/${pk}/`,
                {
                    fields: {
                        quantity: {},
                    },
                    title: '{% trans "Edit Stock Allocation" %}',
                    onSuccess: function() {
                        // Refresh the parent table
                        $(options.table).bootstrapTable('refresh');
                    },
                },
            );
        });

        // Add callbacks for 'delete' buttons
        table.find('.button-allocation-delete').click(function() {
            var pk = $(this).attr('pk');
            
            constructForm(
                `/api/order/so-allocation/${pk}/`,
                {
                    method: 'DELETE',
                    confirmMessage: '{% trans "Confirm Delete Operation" %}',
                    title: '{% trans "Delete Stock Allocation" %}',
                    onSuccess: function() {
                        // Refresh the parent table
                        $(options.table).bootstrapTable('refresh');
                    }
                }
            );
        });
    }

    table.bootstrapTable({
        onPostBody: setupCallbacks,
        data: row.allocations,
        showHeader: false,
        columns: [
            {
                field: 'allocated',
                title: '{% trans "Quantity" %}',
                formatter: function(value, row, index, field) {
                    var text = '';

                    if (row.serial != null && row.quantity == 1) {
                        text = `{% trans "Serial Number" %}: ${row.serial}`;
                    } else {
                        text = `{% trans "Quantity" %}: ${row.quantity}`;
                    }

                    return renderLink(text, `/stock/item/${row.item}/`);
                },
            },
            {
                field: 'location',
                title: '{% trans "Location" %}',
                formatter: function(value, row, index, field) {

                    // Location specified
                    if (row.location) {
                        return renderLink(
                            row.location_detail.pathstring || '{% trans "Location" %}',
                            `/stock/location/${row.location}/`
                        );
                    } else {
                        return `<i>{% trans "Stock location not specified" %}`;
                    }
                },
            },
            // TODO: ?? What is 'po' field all about?
            /*
            {
                field: 'po'
            },
            */
            {
                field: 'buttons',
                title: '{% trans "Actions" %}',
                formatter: function(value, row, index, field) {

                    var html = `<div class='btn-group float-right' role='group'>`;
                    var pk = row.pk;

                    if (pending) {
                        html += makeIconButton('fa-edit icon-blue', 'button-allocation-edit', pk, '{% trans "Edit stock allocation" %}');
                        html += makeIconButton('fa-trash-alt icon-red', 'button-allocation-delete', pk, '{% trans "Delete stock allocation" %}');
                    }

                    html += '</div>';

                    return html;
                },
            },
        ],
    });
}

/**
 * Display a "fulfilled" sub table, showing stock items fulfilled against a purchase order
 */
function showFulfilledSubTable(index, row, element, options) {
    // Construct a table showing stock items which have been fulfilled against this line item

    if (!options.order) {
        return 'ERROR: Order ID not supplied';
    }

    var id = `fulfilled-table-${row.pk}`;
    
    var html = `
    <div class='sub-table'>
        <table class='table table-striped table-condensed' id='${id}'>
        </table>
    </div>`;

    element.html(html);

    $(`#${id}`).bootstrapTable({
        url: '{% url "api-stock-list" %}',
        queryParams: {
            part: row.part,
            sales_order: options.order,
        },
        showHeader: false,
        columns: [
            {
                field: 'pk',
                visible: false,
            },
            {
                field: 'stock',
                formatter: function(value, row) {
                    var text = '';
                    if (row.serial && row.quantity == 1) {
                        text = `{% trans "Serial Number" %}: ${row.serial}`;
                    } else {
                        text = `{% trans "Quantity" %}: ${row.quantity}`;
                    }

                    return renderLink(text, `/stock/item/${row.pk}/`);
                },
            },
            /*
            {
                field: 'po'
            },
            */
        ],
    });
}


/**
 * Load a table displaying line items for a particular SalesOrder
 * 
 * @param {String} table : HTML ID tag e.g. '#table'
 * @param {Object} options : object which contains:
 *      - order {integer} : pk of the SalesOrder
 *      - status: {integer} : status code for the order
 */
function loadSalesOrderLineItemTable(table, options={}) {

    options.table = table;

    options.params = options.params || {};

    if (!options.order) {
        console.log('ERROR: function called without order ID');
        return;
    }

    if (!options.status) {
        console.log('ERROR: function called without order status');
        return;
    }

    options.params.order = options.order;
    options.params.part_detail = true;
    options.params.allocations = true;
    
    var filters = loadTableFilters('salesorderlineitem');

    for (var key in options.params) {
        filters[key] = options.params[key];
    }

    options.url = options.url || '{% url "api-so-line-list" %}';

    var filter_target = options.filter_target || '#filter-list-sales-order-lines';

    setupFilterList('salesorderlineitems', $(table), filter_target);

    // Is the order pending?
    var pending = options.status == {{ SalesOrderStatus.PENDING }};

    // Has the order shipped?
    var shipped = options.status == {{ SalesOrderStatus.SHIPPED }};

    // Show detail view if the PurchaseOrder is PENDING or SHIPPED
    var show_detail = pending || shipped;

    // Table columns to display
    var columns = [
        /*
        {
            checkbox: true,
            visible: true,
            switchable: false,
        },
        */
        {
            sortable: true,
            sortName: 'part__name',
            field: 'part',
            title: '{% trans "Part" %}',
            switchable: false,
            formatter: function(value, row, index, field) {
                if (row.part) {
                    return imageHoverIcon(row.part_detail.thumbnail) + renderLink(row.part_detail.full_name, `/part/${value}/`);
                } else {
                    return '-';
                }
            },
            footerFormatter: function() {
                return '{% trans "Total" %}';
            },
        },
        {
            sortable: true,
            field: 'reference',
            title: '{% trans "Reference" %}',
            switchable: true,
        },
        {
            sortable: true,
            field: 'quantity',
            title: '{% trans "Quantity" %}',
            footerFormatter: function(data) {
                return data.map(function(row) {
                    return +row['quantity'];
                }).reduce(function(sum, i) {
                    return sum + i;
                }, 0);
            },
            switchable: false,
        },
        {
            sortable: true,
            field: 'sale_price',
            title: '{% trans "Unit Price" %}',
            formatter: function(value, row) {
                var formatter = new Intl.NumberFormat(
                    'en-US',
                    {
                        style: 'currency',
                        currency: row.sale_price_currency
                    }
                );

                return formatter.format(row.sale_price);
            }
        },
        {
            field: 'total_price',
            sortable: true,
            title: '{% trans "Total Price" %}',
            formatter: function(value, row) {
                var formatter = new Intl.NumberFormat(
                    'en-US',
                    {
                        style: 'currency',
                        currency: row.sale_price_currency
                    }
                );

                return formatter.format(row.sale_price * row.quantity);
            },
            footerFormatter: function(data) {
                var total = data.map(function(row) {
                    return +row['sale_price'] * row['quantity'];
                }).reduce(function(sum, i) {
                    return sum + i;
                }, 0);

                var currency = (data.slice(-1)[0] && data.slice(-1)[0].sale_price_currency) || 'USD';
                
                var formatter = new Intl.NumberFormat(
                    'en-US',
                    {
                        style: 'currency', 
                        currency: currency
                    }
                );
                
                return formatter.format(total);
            }
        },
    ];

    if (pending) {
        columns.push(
            {
                field: 'stock',
                title: '{% trans "In Stock" %}',
                formatter: function(value, row) {
                    return row.part_detail.stock;
                },
            },
        );
    }

    columns.push(
        {
            field: 'allocated',
            title: pending ? '{% trans "Allocated" %}' : '{% trans "Fulfilled" %}',
            switchable: false,
            formatter: function(value, row, index, field) {

                var quantity = pending ? row.allocated : row.fulfilled;
                return makeProgressBar(quantity, row.quantity, {
                    id: `order-line-progress-${row.pk}`,
                });
            },
            sorter: function(valA, valB, rowA, rowB) {

                var A = pending ? rowA.allocated : rowA.fulfilled;
                var B = pending ? rowB.allocated : rowB.fulfilled;

                if (A == 0 && B == 0) {
                    return (rowA.quantity > rowB.quantity) ? 1 : -1;
                }

                var progressA = parseFloat(A) / rowA.quantity;
                var progressB = parseFloat(B) / rowB.quantity;

                return (progressA < progressB) ? 1 : -1;
            }
        },
        {
            field: 'notes',
            title: '{% trans "Notes" %}',
        },
    );

    if (pending) {
        columns.push({
            field: 'buttons',
            switchable: false,
            formatter: function(value, row, index, field) {

                var html = `<div class='btn-group float-right' role='group'>`;

                var pk = row.pk;

                if (row.part) {
                    var part = row.part_detail;

                    if (part.trackable) {
                        html += makeIconButton('fa-hashtag icon-green', 'button-add-by-sn', pk, '{% trans "Allocate serial numbers" %}');
                    }

                    html += makeIconButton('fa-sign-in-alt icon-green', 'button-add', pk, '{% trans "Allocate stock" %}');

                    if (part.purchaseable) {
                        html += makeIconButton('fa-shopping-cart', 'button-buy', row.part, '{% trans "Purchase stock" %}');
                    }

                    if (part.assembly) {
                        html += makeIconButton('fa-tools', 'button-build', row.part, '{% trans "Build stock" %}');
                    }

                    html += makeIconButton('fa-dollar-sign icon-green', 'button-price', pk, '{% trans "Calculate price" %}');
                }

                html += makeIconButton('fa-edit icon-blue', 'button-edit', pk, '{% trans "Edit line item" %}');
                html += makeIconButton('fa-trash-alt icon-red', 'button-delete', pk, '{% trans "Delete line item " %}');

                html += `</div>`;

                return html;
            }
        });
    }

    function reloadTable() {
        $(table).bootstrapTable('refresh');
    }

    // Configure callback functions once the table is loaded
    function setupCallbacks() {

        // Callback for editing line items
        $(table).find('.button-edit').click(function() {
            var pk = $(this).attr('pk');

            constructForm(`/api/order/so-line/${pk}/`, {
                fields: {
                    quantity: {},
                    reference: {},
                    sale_price: {},
                    sale_price_currency: {},
                    notes: {},
                },
                title: '{% trans "Edit Line Item" %}',
                onSuccess: reloadTable,
            });
        });

        // Callback for deleting line items
        $(table).find('.button-delete').click(function() {
            var pk = $(this).attr('pk');

            constructForm(`/api/order/so-line/${pk}/`, {
                method: 'DELETE',
                title: '{% trans "Delete Line Item" %}',
                onSuccess: reloadTable,
            });
        });

        // Callback for allocating stock items by serial number
        $(table).find('.button-add-by-sn').click(function() {
            var pk = $(this).attr('pk');

            // TODO: Migrate this form to the API forms
            inventreeGet(`/api/order/so-line/${pk}/`, {},
                {
                    success: function(response) {
                        launchModalForm('{% url "so-assign-serials" %}', {
                            success: reloadTable,
                            data: {
                                line: pk,
                                part: response.part, 
                            }
                        });
                    }
                }
            );
        });

        // Callback for allocation stock items to the order
        $(table).find('.button-add').click(function() {
            var pk = $(this).attr('pk');

            var line_item = $(table).bootstrapTable('getRowByUniqueId', pk);

            // Quantity remaining to be allocated
            var remaining = (line_item.quantity || 0) - (line_item.allocated || 0);

            if (remaining < 0) {
                remaining = 0;
            }

            var fields = {
                // SalesOrderLineItem reference
                line: {
                    hidden: true,
                    value: pk,
                },
                item: {
                    filters: {
                        part_detail: true,
                        location_detail: true,
                        in_stock: true,
                        part: line_item.part,
                        exclude_so_allocation: options.order,
                    },
                    auto_fill: true,
                    onSelect: function(data, field, opts) {
                        // Quantity available from this stock item

                        if (!('quantity' in data)) {
                            return;
                        }

                        // Calculate the available quantity
                        var available = Math.max((data.quantity || 0) - (data.allocated || 0), 0);

                        // Maximum amount that we need
                        var desired = Math.min(available, remaining);

                        updateFieldValue('quantity', desired, {}, opts);
                    }
                },
                quantity: {
                    value: remaining,
                },
            };

            // Exclude expired stock?
            if (global_settings.STOCK_ENABLE_EXPIRY && !global_settings.STOCK_ALLOW_EXPIRED_SALE) {
                fields.item.filters.expired = false;
            }

            constructForm(
                `/api/order/so-allocation/`,
                {
                    method: 'POST',
                    fields: fields,
                    title: '{% trans "Allocate Stock Item" %}',
                    onSuccess: reloadTable,
                }
            );
        });

        // Callback for creating a new build
        $(table).find('.button-build').click(function() {
            var pk = $(this).attr('pk');

            // Extract the row data from the table!
            var idx = $(this).closest('tr').attr('data-index');
    
            var row = $(table).bootstrapTable('getData')[idx];
    
            var quantity = 1;
    
            if (row.allocated < row.quantity) {
                quantity = row.quantity - row.allocated;
            }

            // Create a new build order
            newBuildOrder({
                part: pk,
                sales_order: options.order,
                quantity: quantity,
                success: reloadTable
            });
        });

        // Callback for purchasing parts
        $(table).find('.button-buy').click(function() {
            var pk = $(this).attr('pk');

            launchModalForm('{% url "order-parts" %}', {
                data: {
                    parts: [
                        pk
                    ],
                },
            });
        });

        // Callback for displaying price
        $(table).find('.button-price').click(function() {
            var pk = $(this).attr('pk');
            var idx = $(this).closest('tr').attr('data-index');
            var row = $(table).bootstrapTable('getData')[idx];

            launchModalForm(
                '{% url "line-pricing" %}',
                {
                    submit_text: '{% trans "Calculate price" %}',
                    data: {
                        line_item: pk,
                        quantity: row.quantity,
                    },
                    buttons: [
                        {
                            name: 'update_price',
                            title: '{% trans "Update Unit Price" %}'
                        },
                    ],
                    success: reloadTable,
                }
            );
        });
    }

    $(table).inventreeTable({
        onPostBody: setupCallbacks,
        name: 'salesorderlineitems',
        sidePagination: 'server',
        formatNoMatches: function() {
            return '{% trans "No matching line items" %}';
        },
        queryParams: filters,
        original: options.params,
        url: options.url,
        showFooter: true,
        uniqueId: 'pk',
        detailView: show_detail,
        detailViewByClick: false,
        detailFilter: function(index, row) {
            if (pending) {
                // Order is pending
                return row.allocated > 0;
            } else {
                return row.fulfilled > 0;
            }
        },
        detailFormatter: function(index, row, element) {
            if (pending) {
                return showAllocationSubTable(index, row, element, options);
            } else {
                return showFulfilledSubTable(index, row, element, options);
            }
        },
        columns: columns,
    });
}
