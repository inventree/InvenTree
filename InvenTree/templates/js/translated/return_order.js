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
    createReturnOrder,
    loadReturnOrderTable,
*/


/*
 * Construct a set of fields for a ReturnOrder form
 */
function returnOrderFields(options={}) {

    let fields = {
        reference: {
            icon: 'fa-hashtag',
        },
        description: {},
        customer: {
            icon: 'fa-user-tie',
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
        link: {
            icon: 'fa-link',
        },
        responsible: {
            icon: 'fa-user',
        }
    };

    return fields;
}


/*
 * Create a new Return Order
 */
function createReturnOrder(options={}) {
    let fields = returnOrderFields(options);

    if (options.customer) {
        fields.customer.value = options.customer;
    }

    constructForm('{% url "api-return-order-list" %}', {
        method: 'POST',
        fields: fields,
        title: '{% trans "Create Return Order" %}',
        onSuccess: function(data) {
            location.href = `/order/return-order/${data.pk}/`;
        },
    });
}


/*
 * Edit an existing Return Order
 */
function editReturnOrder(order_id, options={}) {

    constructForm(`/api/order/return/${order_id}/`, {
        fields: returnOrderFields(options),
        title: '{% trans "Edit Return Order" %}',
        onSuccess: function(response) {
            handleFormSuccess(response, options);
        }
    });
}


/*
 * Load a table of return orders
 */
function loadReturnOrderTable(table, options={}) {

    // Ensure the table starts in a known state
    $(table).bootstrapTable('destroy');

    options.params = options.params || {};
    options.params['customer_detail'] = true;

    var filters = loadTableFilters('returnorder');

    for (var key in options.params) {
        filters[key] = options.params[key];
    }

    setupFilterList('returnorder', $(table), '#filter-list-returnorder', {download: true});

    let display_mode = inventreeLoad('returnorder-table-display-mode', 'list');

    let is_calendar = display_mode == 'calendar';

    $(table).inventreeTable({
        url: '{% url "api-return-order-list" %}',
        queryParams: filters,
        name: 'returnorder',
        sidePagination: 'server',
        original: options.params,
        showColumns: !is_calendar,
        search: !is_calendar,
        showCustomViewButton: false,
        showCustomView: is_calendar,
        disablePagination: is_calendar,
        formatNoMatches: function() {
            return '{% trans "No return orders found" %}';
        },
        onRefresh: function() {
            loadReturnOrderTable(table, options);
        },
        onLoadSuccess: function() {
            // TODO
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
                title: '{% trans "Return Order" %}',
                formatter: function(value, row) {
                    var html = renderLink(value, `/order/return-order/${row.pk}/`);
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
                    return returnOrderStatusDisplay(row.status);
                }
            },
            {
                sortable: true,
                field: 'creation_date',
                title: '{% trans "Creation Date" %}',
                formatter: function(value) {
                    return renderDate(value);
                }
            },
            {
                field: 'responsible',
                title: '{% trans "Responsible" %}',
                switchable: true,
                sortable: true,
                formatter: function(value, row) {
                    if (!row.responsible_detail) {
                        return '-';
                    }

                    let html = row.responsible_detail.name;

                    if (row.responsible_detail.label == 'group') {
                        html += `<span class='float-right fas fa-users'></span>`;
                    } else {
                        html += `<span class='float-right fas fa-user'></span>`;
                    }

                    return html;
                }
            }
        ]
    });
}
