{% load i18n %}
{% load inventree_extras %}

/* globals
    companyFormFields,
    constructForm,
    imageHoverIcon,
    loadTableFilters,
    renderLink,
    returnOrderStatusDisplay,
    setupFilterList,
*/

/* exported
    createReturnOrder,
    createReturnOrderLineItem,
    editReturnOrder,
    editReturnOrderLineItem,
    loadReturnOrderTable,
    loadReturnOrderLineItemTable,
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
        target_date: {
            icon: 'fa-calendar-alt',
        },
        link: {
            icon: 'fa-link',
        },
        contact: {
            icon: 'fa-user',
            adjustFilters: function(filters) {
                let customer = getFormFieldValue('customer', {}, {modal: options.modal});

                if (customer) {
                    filters.company = customer;
                }

                return filters;
            }
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

    constructForm(`{% url "api-return-order-list" %}${order_id}/`, {
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

    let filters = loadTableFilters('returnorder', options.params);

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
                    let html = renderLink(value, `/order/return-order/${row.pk}/`);

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
                sortable: true,
                field: 'target_date',
                title: '{% trans "Target Date" %}',
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


/*
 * Construct a set of fields for a ReturnOrderLineItem form
 */
function returnOrderLineItemFields(options={}) {

    let fields = {
        order: {
            filters: {
                customer_detail: true,
            }
        },
        item: {
            filters: {
                part_detail: true,
                serialized: true,
            }
        },
        reference: {},
        price: {
            icon: 'fa-dollar-sign',
        },
        price_currency: {
            icone: 'fa-coins',
        },
        target_date: {
            icon: 'fa-calendar-alt',
        },
        notes: {
            icon: 'fa-sticky-note',
        }
    };

    return fields;
}


/*
 * Create a new ReturnOrderLineItem
 */
function createReturnOrderLineItem(options={}) {

    let fields = returnOrderLineItemFields();

    if (options.order) {
        fields.order.value = options.order;
        fields.order.hidden = true;
    }

    if (options.customer) {
        Object.assign(fields.item.filters, {
            customer: options.customer
        });
    }

    constructForm('{% url "api-return-order-line-list" %}', {
        fields: fields,
        method: 'POST',
        title: '{% trans "Add Line Item" %}',
        onSuccess: function(response) {
            handleFormSuccess(response, options);
        }
    });
}


/*
 * Edit an existing ReturnOrderLineItem
 */
function editReturnOrderLineItem(pk, options={}) {

    let fields = returnOrderLineItemFields();

    constructForm(`{% url "api-return-order-line-list" %}${pk}/`, {
        fields: fields,
        title: '{% trans "Edit Line Item" %}',
        onSuccess: function(response) {
            handleFormSuccess(response, options);
        }
    });
}


/*
 * Load a table displaying line items for a particular ReturnOrder
 */
function loadReturnOrderLineItemTable(options={}) {

    var table = options.table;

    options.params = options.params || {};

    options.params.order = options.order;
    options.params.item_detail = true;
    options.params.order_detail = false;

    let filters = loadTableFilters('returnorderlineitem', options.params);

    setupFilterList('returnorderlines', $(table), '#filter-list-returnorderlines', {download: true});

    function setupCallbacks() {
        // TODO
    }

    $(table).inventreeTable({
        url: '{% url "api-return-order-line-list" %}',
        name: 'returnorderlineitems',
        formatNoMatches: function() {
            return '{% trans "No matching line items" %}';
        },
        onPostBody: setupCallbacks,
        queryParams: filters,
        original: options.params,
        showColumns: true,
        showFooter: true,
        uniqueId: 'pk',
        columns: [
            {
                checkbox: true,
                switchable: false,
            },
            {
                field: 'item',
                sortable: true,
                title: '{% trans "Item" %}',
                formatter: function(value, row) {
                    return `item: ${value}`;
                }
            },
            {
                field: 'reference',
                title: '{% trans "Reference" %}',
            },
            {
                field: 'price',
                title: '{% trans "Price" %}',
                formatter: function(value, row) {
                    return formatCurrency(row.price, {
                        currency: row.price_currency,
                    });
                }
            },
            {
                sortable: true,
                field: 'target_date',
                title: '{% trans "Target Date" %}',
                formatter: function(value, row) {
                    let html = renderDate(value);

                    if (row.overdue) {
                        html += `<span class='fas fa-calendar-times icon-red float-right' title='{% trans "This line item is overdue" %}'></span>`;
                    }

                    return html;
                }
            },
            {
                field: 'received',
                title: '{% trans "Received" %}',
            },
            {
                field: 'notes',
                title: '{% trans "Notes" %}',
            },
            {
                field: 'buttons',
                title: '',
                switchable: false,
                formatter: function(value, row) {
                    return `buttons ${row.pk}`;
                }
            }
        ]
    });
}
