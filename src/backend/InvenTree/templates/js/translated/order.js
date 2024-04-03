{% load i18n %}
{% load inventree_extras %}

/* globals
    calculateTotalPrice,
    constructForm,
    constructFormBody,
    exportFormatOptions,
    formatCurrency,
    getFormFieldValue,
    inventreeGet,
    inventreeLoad,
    inventreeSave,
    loadTableFilters,
    makeCopyButton,
    makeDeleteButton,
    makeEditButton,
    reloadBootstrapTable,
    renderLink,
    setupFilterList,
    wrapButtons,
*/

/* exported
    createExtraLineItem,
    editExtraLineItem,
    exportOrder,
    issuePurchaseOrder,
    newPurchaseOrderFromOrderWizard,
    newSupplierPartFromOrderWizard,
    orderParts,
    removeOrderRowFromOrderWizard,
    removePurchaseOrderLineItem,
    loadOrderTotal,
    loadExtraLineTable,
    extraLineFields,
    reloadTotal,
*/


/* Construct a set of fields for a OrderExtraLine form */
function extraLineFields(options={}) {

    var fields = {
        order: {
            hidden: true,
        },
        quantity: {},
        reference: {},
        description: {},
        price: {
            icon: 'fa-dollar-sign',
        },
        price_currency: {
            icon: 'fa-coins',
        },
        notes: {
            icon: 'fa-sticky-note',
        },
        link: {
            icon: 'fa-link',
        }
    };

    if (options.order) {
        fields.order.value = options.order;
    }

    return fields;
}


/*
 * Create a new ExtraLineItem
 */
function createExtraLineItem(options={}) {

    let fields = extraLineFields({
        order: options.order,
    });

    if (options.currency) {
        fields.price_currency.value = options.currency;
    }

    constructForm(options.url, {
        fields: fields,
        method: 'POST',
        title: '{% trans "Add Extra Line Item" %}',
        onSuccess: function(response) {
            if (options.table) {
                reloadBootstrapTable(options.table);
            }
        }
    });
}


/* Remove a part selection from an order form. */
function removeOrderRowFromOrderWizard(e) {

    e = e || window.event;

    var src = e.target || e.srcElement;

    var row = $(src).attr('row');

    $('#' + row).remove();
}

/**
 * Export an order (PurchaseOrder or SalesOrder)
 *
 * - Display a simple form which presents the user with export options
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


var TotalPriceRef = ''; // reference to total price field
var TotalPriceOptions = {}; // options to reload the price


function loadOrderTotal(reference, options={}) {
    TotalPriceRef = reference;
    TotalPriceOptions = options;
}


function reloadTotal() {
    inventreeGet(
        TotalPriceOptions.url,
        {},
        {
            success: function(data) {
                $(TotalPriceRef).html(formatCurrency(data.price, {currency: data.price_currency}));
            }
        }
    );
}


/*
 * Load a table displaying "extra" line items for a given order.
 * Used for all external order types (e.g. PurchaseOrder / SalesOrder / ReturnOrder)
 *
 * options:
 *  - table: The DOM ID of the table element
 *  - order: The ID of the related order (required)
 *  - name: The unique 'name' for this table
 *  - url: The API URL for the extra line item model (required)
 *  - filtertarget: The DOM ID for the filter list element
 */
function loadExtraLineTable(options={}) {

    const table = options.table;

    options.params = options.params || {};

    // Filtering
    options.params.order = options.order;

    var filters = {};

    if (options.name) {
        filters = loadTableFilters(options.name);
    }

    Object.assign(filters, options.params);

    setupFilterList(
        options.name,
        $(table),
        options.filtertarget,
        {
            download: true
        }
    );

    // Helper function to reload table
    function reloadExtraLineTable() {
        $(table).bootstrapTable('refresh');

        if (options.pricing) {
            reloadTotal();
        }
    }

    // Configure callback functions once the table is loaded
    function setupCallbacks() {

        if (options.allow_edit) {

            // Callback to duplicate line item
            $(table).find('.button-duplicate').click(function() {
                var pk = $(this).attr('pk');

                inventreeGet(`${options.url}${pk}/`, {}, {
                    success: function(data) {

                        var fields = extraLineFields();

                        constructForm(options.url, {
                            method: 'POST',
                            fields: fields,
                            data: data,
                            title: '{% trans "Duplicate Line" %}',
                            onSuccess: reloadExtraLineTable,
                        });
                    }
                });
            });

            // Callback to edit line item
            // Callback for editing lines
            $(table).find('.button-edit').click(function() {
                var pk = $(this).attr('pk');

                constructForm(`${options.url}${pk}/`, {
                    fields: extraLineFields(),
                    title: '{% trans "Edit Line" %}',
                    onSuccess: reloadExtraLineTable,
                });
            });
        }

        if (options.allow_delete) {
            // Callback for deleting lines
            $(table).find('.button-delete').click(function() {
                var pk = $(this).attr('pk');

                constructForm(`${options.url}${pk}/`, {
                    method: 'DELETE',
                    title: '{% trans "Delete Line" %}',
                    onSuccess: reloadExtraLineTable,
                });
            });
        }
    }

    $(table).inventreeTable({
        url: options.url,
        name: options.name,
        sidePagination: 'server',
        onPostBody: setupCallbacks,
        formatNoMatches: function() {
            return '{% trans "No line items found" %}';
        },
        queryParams: filters,
        original: options.params,
        showFooter: true,
        uniqueId: 'pk',
        columns: [
            {
                sortable: true,
                field: 'reference',
                title: '{% trans "Reference" %}',
                switchable: false,
            },
            {
                sortable: false,
                switchable: true,
                field: 'description',
                title: '{% trans "Description" %}',
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
                },
            },
            {
                sortable: true,
                field: 'price',
                title: '{% trans "Unit Price" %}',
                formatter: function(value, row) {
                    return formatCurrency(row.price, {
                        currency: row.price_currency,
                    });
                }
            },
            {
                field: 'total_price',
                sortable: true,
                switchable: true,
                title: '{% trans "Total Price" %}',
                formatter: function(value, row) {
                    return formatCurrency(row.price * row.quantity, {
                        currency: row.price_currency,
                    });
                },
                footerFormatter: function(data) {
                    return calculateTotalPrice(
                        data,
                        function(row) {
                            return row.price ? row.price * row.quantity : null;
                        },
                        function(row) {
                            return row.price_currency;
                        }
                    );
                }
            },
            {
                field: 'notes',
                title: '{% trans "Notes" %}',
            },
            {
                field: 'link',
                title: '{% trans "Link" %}',
                formatter: function(value) {
                    if (value) {
                        return renderLink(value, value);
                    }
                }
            },
            {
                field: 'buttons',
                switchable: false,
                formatter: function(value, row, index, field) {

                    let html = '';

                    if (options.allow_edit || options.allow_delete) {
                        var pk = row.pk;

                        if (options.allow_edit) {
                            html += makeCopyButton('button-duplicate', pk, '{% trans "Duplicate line" %}');
                            html += makeEditButton('button-edit', pk, '{% trans "Edit line" %}');
                        }

                        if (options.allow_delete) {
                            html += makeDeleteButton('button-delete', pk, '{% trans "Delete line" %}', );
                        }
                    }

                    return wrapButtons(html);
                }
            },
        ]
    });
}
