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
    supplierPartFields,
*/

/* exported
    exportOrder,
    issuePurchaseOrder,
    newPurchaseOrderFromOrderWizard,
    newSupplierPartFromOrderWizard,
    orderParts,
    removeOrderRowFromOrderWizard,
    removePurchaseOrderLineItem,
    loadOrderTotal,
    extraLineFields,
*/


/* Construct a set of fields for a OrderExtraLine form */
function extraLineFields(options={}) {

    var fields = {
        order: {
            hidden: true,
        },
        quantity: {},
        reference: {},
        price: {
            icon: 'fa-dollar-sign',
        },
        price_currency: {
            icon: 'fa-coins',
        },
        notes: {
            icon: 'fa-sticky-note',
        },
    };

    if (options.order) {
        fields.order.value = options.order;
    }

    return fields;
}



function removeOrderRowFromOrderWizard(e) {
    /* Remove a part selection from an order form. */

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
};
