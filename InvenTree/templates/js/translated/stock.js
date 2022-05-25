{% load i18n %}
{% load inventree_extras %}
{% load status_codes %}

/* globals
    attachSelect,
    closeModal,
    constructField,
    constructFormBody,
    getFormFieldValue,
    global_settings,
    handleFormErrors,
    imageHoverIcon,
    inventreeDelete,
    inventreeGet,
    inventreePut,
    launchModalForm,
    linkButtonsToSelection,
    loadTableFilters,
    makeIconBadge,
    makeIconButton,
    makeOptionsList,
    makePartIcons,
    modalEnable,
    modalSetContent,
    modalSetTitle,
    modalSubmit,
    openModal,
    printStockItemLabels,
    printTestReports,
    renderLink,
    scanItemsIntoLocation,
    showAlertDialog,
    setupFilterList,
    showApiError,
    stockStatusDisplay,
*/

/* exported
    assignStockToCustomer,
    createNewStockItem,
    createStockLocation,
    duplicateStockItem,
    editStockItem,
    editStockLocation,
    findStockItemBySerialNumber,
    installStockItem,
    loadInstalledInTable,
    loadStockLocationTable,
    loadStockTable,
    loadStockTestResultsTable,
    loadStockTrackingTable,
    loadTableFilters,
    mergeStockItems,
    removeStockRow,
    serializeStockItem,
    stockItemFields,
    stockLocationFields,
    stockStatusCodes,
    uninstallStockItem,
*/


/*
 * Launches a modal form to serialize a particular StockItem
 */

function serializeStockItem(pk, options={}) {

    var url = `/api/stock/${pk}/serialize/`;

    options.method = 'POST';
    options.title = '{% trans "Serialize Stock Item" %}';

    options.fields = {
        quantity: {},
        serial_numbers: {
            icon: 'fa-hashtag',
        },
        destination: {
            icon: 'fa-sitemap',
        },
        notes: {},
    };

    if (options.part) {
        // Work out the next available serial number
        inventreeGet(`/api/part/${options.part}/serial-numbers/`, {}, {
            success: function(data) {
                if (data.next) {
                    options.fields.serial_numbers.placeholder = `{% trans "Next available serial number" %}: ${data.next}`;
                } else if (data.latest) {
                    options.fields.serial_numbers.placeholder = `{% trans "Latest serial number" %}: ${data.latest}`;
                }
            },
            async: false,
        });
    }

    options.confirm = true;
    options.confirmMessage = '{% trans "Confirm Stock Serialization" %}';

    constructForm(url, options);
}


function stockLocationFields(options={}) {
    var fields = {
        parent: {
            help_text: '{% trans "Parent stock location" %}',
            required: false,
        },
        name: {},
        description: {},
        owner: {},
    };

    if (options.parent) {
        fields.parent.value = options.parent;
    }

    if (!global_settings.STOCK_OWNERSHIP_CONTROL) {
        delete fields['owner'];
    }

    return fields;
}


/*
 * Launch an API form to edit a stock location
 */
function editStockLocation(pk, options={}) {

    var url = `/api/stock/location/${pk}/`;

    options.fields = stockLocationFields(options);

    options.title = '{% trans "Edit Stock Location" %}';

    constructForm(url, options);
}


/*
 * Launch an API form to create a new stock location
 */
function createStockLocation(options={}) {

    var url = '{% url "api-location-list" %}';

    options.method = 'POST';
    options.fields = stockLocationFields(options);
    options.title = '{% trans "New Stock Location" %}';

    constructForm(url, options);
}


function stockItemFields(options={}) {
    var fields = {
        part: {
            // Hide the part field unless we are "creating" a new stock item
            hidden: !options.create,
            onSelect: function(data, field, opts) {
                // Callback when a new "part" is selected

                // If we are "creating" a new stock item,
                // change the available fields based on the part properties
                if (options.create) {

                    // If a "trackable" part is selected, enable serial number field
                    if (data.trackable) {
                        enableFormInput('serial_numbers', opts);

                        // Request part serial number information from the server
                        inventreeGet(`/api/part/${data.pk}/serial-numbers/`, {}, {
                            success: function(data) {
                                var placeholder = '';
                                if (data.next) {
                                    placeholder = `{% trans "Next available serial number" %}: ${data.next}`;
                                } else if (data.latest) {
                                    placeholder = `{% trans "Latest serial number" %}: ${data.latest}`;
                                }

                                setFormInputPlaceholder('serial_numbers', placeholder, opts);
                            }
                        });

                    } else {
                        clearFormInput('serial_numbers', opts);
                        disableFormInput('serial_numbers', opts);

                        setFormInputPlaceholder('serial_numbers', '{% trans "This part cannot be serialized" %}', opts);
                    }

                    // Enable / disable fields based on purchaseable status
                    if (data.purchaseable) {
                        enableFormInput('supplier_part', opts);
                        enableFormInput('purchase_price', opts);
                        enableFormInput('purchase_price_currency', opts);
                    } else {
                        clearFormInput('supplier_part', opts);
                        clearFormInput('purchase_price', opts);

                        disableFormInput('supplier_part', opts);
                        disableFormInput('purchase_price', opts);
                        disableFormInput('purchase_price_currency', opts);
                    }
                }
            }
        },
        supplier_part: {
            icon: 'fa-building',
            filters: {
                part_detail: true,
                supplier_detail: true,
            },
            adjustFilters: function(query, opts) {
                var part = getFormFieldValue('part', {}, opts);

                if (part) {
                    query.part = part;
                }

                return query;
            }
        },
        location: {
            icon: 'fa-sitemap',
        },
        quantity: {
            help_text: '{% trans "Enter initial quantity for this stock item" %}',
        },
        serial_numbers: {
            icon: 'fa-hashtag',
            type: 'string',
            label: '{% trans "Serial Numbers" %}',
            help_text: '{% trans "Enter serial numbers for new stock (or leave blank)" %}',
            required: false,
        },
        serial: {
            icon: 'fa-hashtag',
        },
        batch: {
            icon: 'fa-layer-group',
        },
        status: {},
        expiry_date: {},
        purchase_price: {
            icon: 'fa-dollar-sign',
        },
        purchase_price_currency: {},
        packaging: {
            icon: 'fa-box',
        },
        link: {
            icon: 'fa-link',
        },
        owner: {},
        delete_on_deplete: {},
    };

    if (options.create) {
        // Use special "serial numbers" field when creating a new stock item
        delete fields['serial'];
    } else {
        // These fields cannot be edited once the stock item has been created
        delete fields['serial_numbers'];
        delete fields['quantity'];
        delete fields['location'];
    }

    // Remove stock expiry fields if feature is not enabled
    if (!global_settings.STOCK_ENABLE_EXPIRY) {
        delete fields['expiry_date'];
    }

    // Remove ownership field if feature is not enanbled
    if (!global_settings.STOCK_OWNERSHIP_CONTROL) {
        delete fields['owner'];
    }

    return fields;
}


function stockItemGroups(options={}) {
    return {

    };
}


/*
 * Launch a modal form to duplicate a given StockItem
 */
function duplicateStockItem(pk, options) {

    // If no "success" function provided, add a default
    if (!options.onSuccess) {
        options.onSuccess = function(response) {

            showAlertOrCache('{% trans "Stock item duplicated" %}', true, {style: 'success'});

            window.location.href = `/stock/item/${response.pk}/`;
        };
    }

    // First, we need the StockItem information
    inventreeGet(`/api/stock/${pk}/`, {}, {
        success: function(data) {

            // Do not duplicate the serial number
            delete data['serial'];

            options.data = data;

            options.create = true;
            options.fields = stockItemFields(options);
            options.groups = stockItemGroups(options);

            options.method = 'POST';
            options.title = '{% trans "Duplicate Stock Item" %}';

            constructForm('{% url "api-stock-list" %}', options);
        }
    });
}


/*
 * Launch a modal form to edit a given StockItem
 */
function editStockItem(pk, options={}) {

    var url = `/api/stock/${pk}/`;

    options.create = false;

    options.fields = stockItemFields(options);
    options.groups = stockItemGroups(options);

    options.title = '{% trans "Edit Stock Item" %}';

    // Query parameters for retrieving stock item data
    options.params = {
        part_detail: true,
        supplier_part_detail: true,
    };

    // Augment the rendered form when we receive information about the StockItem
    options.processResults = function(data, fields, options) {
        if (data.part_detail.trackable) {
            delete options.fields.delete_on_deplete;
        } else {
            // Remove serial number field if part is not trackable
            delete options.fields.serial;
        }

        // Remove pricing fields if part is not purchaseable
        if (!data.part_detail.purchaseable) {
            delete options.fields.supplier_part;
            delete options.fields.purchase_price;
            delete options.fields.purchase_price_currency;
        }
    };

    constructForm(url, options);
}


/*
 * Launch an API form to contsruct a new stock item
 */
function createNewStockItem(options={}) {

    var url = '{% url "api-stock-list" %}';

    options.title = '{% trans "New Stock Item" %}';
    options.method = 'POST';

    options.create = true;

    options.fields = stockItemFields(options);
    options.groups = stockItemGroups(options);

    if (!options.onSuccess) {
        options.onSuccess = function(response) {
            // If a single stock item has been created, follow it!
            if (response.pk) {
                var url = `/stock/item/${response.pk}/`;

                addCachedAlert('{% trans "Created new stock item" %}', {
                    icon: 'fas fa-boxes',
                });

                window.location.href = url;
            } else {

                // Multiple stock items have been created (i.e. serialized stock)
                var details = `
                <br>{% trans "Quantity" %}: ${response.quantity}
                <br>{% trans "Serial Numbers" %}: ${response.serial_numbers}
                `;

                showMessage('{% trans "Created multiple stock items" %}', {
                    icon: 'fas fa-boxes',
                    details: details,
                });

                var table = options.table || '#stock-table';

                // Reload the table
                $(table).bootstrapTable('refresh');
            }
        };
    }

    constructForm(url, options);
}

/*
 * Launch a modal form to find a particular stock item by serial number.
 * Arguments:
 * - part: ID (PK) of the part in question
 */

function findStockItemBySerialNumber(part_id) {

    constructFormBody({}, {
        title: '{% trans "Find Serial Number" %}',
        fields: {
            serial: {
                label: '{% trans "Serial Number" %}',
                help_text: '{% trans "Enter serial number" %}',
                placeholder: '{% trans "Enter serial number" %}',
                required: true,
                type: 'string',
                value: '',
            }
        },
        onSubmit: function(fields, opts) {

            var serial = getFormFieldValue('serial', fields['serial'], opts);

            serial = serial.toString().trim();

            if (!serial) {
                handleFormErrors(
                    {
                        'serial': [
                            '{% trans "Enter a serial number" %}',
                        ]
                    }, fields, opts
                );
                return;
            }

            inventreeGet(
                '{% url "api-stock-list" %}',
                {
                    part_tree: part_id,
                    serial: serial,
                },
                {
                    success: function(response) {
                        if (response.length == 0) {
                            // No results!
                            handleFormErrors(
                                {
                                    'serial': [
                                        '{% trans "No matching serial number" %}',
                                    ]
                                }, fields, opts
                            );
                        } else if (response.length > 1) {
                            // Too many results!
                            handleFormErrors(
                                {
                                    'serial': [
                                        '{% trans "More than one matching result found" %}',
                                    ]
                                }, fields, opts
                            );
                        } else {
                            $(opts.modal).modal('hide');

                            // Redirect
                            var pk = response[0].pk;
                            location.href = `/stock/item/${pk}/`;
                        }
                    },
                    error: function(xhr) {
                        showApiError(xhr, opts.url);
                        $(opts.modal).modal('hide');
                    }
                }
            );
        }
    });
}


/* Stock API functions
 * Requires api.js to be loaded first
 */

function stockStatusCodes() {
    return [
        {% for code in StockStatus.list %}
        {
            key: {{ code.key }},
            text: '{{ code.value }}',
        },
        {% endfor %}
    ];
}


/**
 * Assign multiple stock items to a customer
 */
function assignStockToCustomer(items, options={}) {

    // Generate HTML content for the form
    var html = `
    <table class='table table-striped table-condensed' id='stock-assign-table'>
    <thead>
        <tr>
            <th>{% trans "Part" %}</th>
            <th>{% trans "Stock Item" %}</th>
            <th>{% trans "Location" %}</th>
            <th></th>
        </tr>
    </thead>
    <tbody>
    `;

    for (var idx = 0; idx < items.length; idx++) {

        var item = items[idx];

        var pk = item.pk;

        var part = item.part_detail;

        var thumbnail = thumbnailImage(part.thumbnail || part.image);

        var status = stockStatusDisplay(item.status, {classes: 'float-right'});

        var quantity = '';

        if (item.serial && item.quantity == 1) {
            quantity = `{% trans "Serial" %}: ${item.serial}`;
        } else {
            quantity = `{% trans "Quantity" %}: ${item.quantity}`;
        }

        quantity += status;

        var location = locationDetail(item, false);

        var buttons = `<div class='btn-group' role='group'>`;

        buttons += makeIconButton(
            'fa-times icon-red',
            'button-stock-item-remove',
            pk,
            '{% trans "Remove row" %}',
        );

        buttons += '</div>';

        html += `
        <tr id='stock_item_${pk}' class='stock-item-row'>
            <td id='part_${pk}'>${thumbnail} ${part.full_name}</td>
            <td id='stock_${pk}'>
                <div id='div_id_items_item_${pk}'>
                    ${quantity}
                    <div id='errors-items_item_${pk}'></div>
                </div>
            </td>
            <td id='location_${pk}'>${location}</td>
            <td id='buttons_${pk}'>${buttons}</td>
        </tr>
        `;
    }

    html += `</tbody></table>`;

    constructForm('{% url "api-stock-assign" %}', {
        method: 'POST',
        preFormContent: html,
        fields: {
            customer: {
                value: options.customer,
                filters: {
                    is_customer: true,
                },
            },
            notes: {},
        },
        confirm: true,
        confirmMessage: '{% trans "Confirm stock assignment" %}',
        title: '{% trans "Assign Stock to Customer" %}',
        afterRender: function(fields, opts) {
            // Add button callbacks to remove rows
            $(opts.modal).find('.button-stock-item-remove').click(function() {
                var pk = $(this).attr('pk');

                $(opts.modal).find(`#stock_item_${pk}`).remove();
            });
        },
        onSubmit: function(fields, opts) {

            // Extract data elements from the form
            var data = {
                customer: getFormFieldValue('customer', {}, opts),
                notes: getFormFieldValue('notes', {}, opts),
                items: [],
            };

            var item_pk_values = [];

            items.forEach(function(item) {
                var pk = item.pk;

                // Does the row exist in the form?
                var row = $(opts.modal).find(`#stock_item_${pk}`);

                if (row.exists()) {
                    item_pk_values.push(pk);

                    data.items.push({
                        item: pk,
                    });
                }
            });

            opts.nested = {
                'items': item_pk_values,
            };

            inventreePut(
                '{% url "api-stock-assign" %}',
                data,
                {
                    method: 'POST',
                    success: function(response) {
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


/**
 * Merge multiple stock items together
 */
function mergeStockItems(items, options={}) {

    // Generate HTML content for the form
    var html = `
    <div class='alert alert-block alert-danger'>
    <h5>{% trans "Warning: Merge operation cannot be reversed" %}</h5>
    <strong>{% trans "Some information will be lost when merging stock items" %}:</strong>
    <ul>
        <li>{% trans "Stock transaction history will be deleted for merged items" %}</li>
        <li>{% trans "Supplier part information will be deleted for merged items" %}</li>
    </ul>
    </div>
    `;

    html += `
    <table class='table table-striped table-condensed' id='stock-merge-table'>
    <thead>
        <tr>
            <th>{% trans "Part" %}</th>
            <th>{% trans "Stock Item" %}</th>
            <th>{% trans "Location" %}</th>
            <th></th>
        </tr>
    </thead>
    <tbody>
    `;

    // Keep track of how many "locations" there are
    var locations = [];

    for (var idx = 0; idx < items.length; idx++) {
        var item = items[idx];

        var pk = item.pk;

        if (item.location && !locations.includes(item.location)) {
            locations.push(item.location);
        }

        var part = item.part_detail;
        var location = locationDetail(item, false);

        var thumbnail = thumbnailImage(part.thumbnail || part.image);

        var quantity = '';

        if (item.serial && item.quantity == 1) {
            quantity = `{% trans "Serial" %}: ${item.serial}`;
        } else {
            quantity = `{% trans "Quantity" %}: ${item.quantity}`;
        }

        quantity += stockStatusDisplay(item.status, {classes: 'float-right'});

        var buttons = `<div class='btn-group' role='group'>`;

        buttons += makeIconButton(
            'fa-times icon-red',
            'button-stock-item-remove',
            pk,
            '{% trans "Remove row" %}',
        );

        html += `
        <tr id='stock_item_${pk}' class='stock-item-row'>
            <td id='part_${pk}'>${thumbnail} ${part.full_name}</td>
            <td id='stock_${pk}'>
                <div id='div_id_items_item_${pk}'>
                    ${quantity}
                    <div id='errors-items_item_${pk}'></div>
                </div>
            </td>
            <td id='location_${pk}'>${location}</td>
            <td id='buttons_${pk}'>${buttons}</td>
        </tr>
        `;
    }

    html += '</tbody></table>';

    var location = locations.length == 1 ? locations[0] : null;

    constructForm('{% url "api-stock-merge" %}', {
        method: 'POST',
        preFormContent: html,
        fields: {
            location: {
                value: location,
                icon: 'fa-sitemap',
            },
            notes: {},
            allow_mismatched_suppliers: {},
            allow_mismatched_status: {},
        },
        confirm: true,
        confirmMessage: '{% trans "Confirm stock item merge" %}',
        title: '{% trans "Merge Stock Items" %}',
        afterRender: function(fields, opts) {
            // Add button callbacks to remove rows
            $(opts.modal).find('.button-stock-item-remove').click(function() {
                var pk = $(this).attr('pk');

                $(opts.modal).find(`#stock_item_${pk}`).remove();
            });
        },
        onSubmit: function(fields, opts) {

            // Extract data elements from the form
            var data = {
                items: [],
            };

            var item_pk_values = [];

            items.forEach(function(item) {
                var pk = item.pk;

                // Does the row still exist in the form?
                var row = $(opts.modal).find(`#stock_item_${pk}`);

                if (row.exists()) {
                    item_pk_values.push(pk);

                    data.items.push({
                        item: pk,
                    });
                }
            });

            var extra_fields = [
                'location',
                'notes',
                'allow_mismatched_suppliers',
                'allow_mismatched_status',
            ];

            extra_fields.forEach(function(field) {
                data[field] = getFormFieldValue(field, fields[field], opts);
            });

            opts.nested = {
                'items': item_pk_values
            };

            // Submit the form data
            inventreePut(
                '{% url "api-stock-merge" %}',
                data,
                {
                    method: 'POST',
                    success: function(response) {
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


/**
 * Perform stock adjustments
 */
function adjustStock(action, items, options={}) {

    var formTitle = 'Form Title Here';
    var actionTitle = null;

    // API url
    var url = null;

    var specifyLocation = false;
    var allowSerializedStock = false;

    switch (action) {
    case 'move':
        formTitle = '{% trans "Transfer Stock" %}';
        actionTitle = '{% trans "Move" %}';
        specifyLocation = true;
        allowSerializedStock = true;
        url = '{% url "api-stock-transfer" %}';
        break;
    case 'count':
        formTitle = '{% trans "Count Stock" %}';
        actionTitle = '{% trans "Count" %}';
        url = '{% url "api-stock-count" %}';
        break;
    case 'take':
        formTitle = '{% trans "Remove Stock" %}';
        actionTitle = '{% trans "Take" %}';
        url = '{% url "api-stock-remove" %}';
        break;
    case 'add':
        formTitle = '{% trans "Add Stock" %}';
        actionTitle = '{% trans "Add" %}';
        url = '{% url "api-stock-add" %}';
        break;
    case 'delete':
        formTitle = '{% trans "Delete Stock" %}';
        allowSerializedStock = true;
        break;
    default:
        break;
    }

    // Generate modal HTML content
    var html = `
    <table class='table table-striped table-condensed' id='stock-adjust-table'>
    <thead>
    <tr>
        <th>{% trans "Part" %}</th>
        <th>{% trans "Stock" %}</th>
        <th>{% trans "Location" %}</th>
        <th>${actionTitle || ''}</th>
        <th></th>
    </tr>
    </thead>
    <tbody>
    `;

    var itemCount = 0;

    for (var idx = 0; idx < items.length; idx++) {

        var item = items[idx];

        if ((item.serial != null) && !allowSerializedStock) {
            continue;
        }

        var pk = item.pk;

        var readonly = (item.serial != null);
        var minValue = null;
        var maxValue = null;
        var value = null;

        switch (action) {
        case 'move':
            minValue = 0;
            maxValue = item.quantity;
            value = item.quantity;
            break;
        case 'add':
            minValue = 0;
            value = 0;
            break;
        case 'take':
            minValue = 0;
            value = 0;
            break;
        case 'count':
            minValue = 0;
            value = item.quantity;
            break;
        default:
            break;
        }

        var thumb = thumbnailImage(item.part_detail.thumbnail || item.part_detail.image);

        var status = stockStatusDisplay(item.status, {
            classes: 'float-right'
        });

        var quantity = item.quantity;

        var location = locationDetail(item, false);

        if (item.location_detail) {
            location = item.location_detail.pathstring;
        }

        if (item.serial != null) {
            quantity = `#${item.serial}`;
        }

        if (item.batch) {
            quantity += ` - <small>{% trans "Batch" %}: ${item.batch}</small>`;
        }

        var actionInput = '';

        if (actionTitle != null) {
            actionInput = constructField(
                `items_quantity_${pk}`,
                {
                    type: 'decimal',
                    min_value: minValue,
                    max_value: maxValue,
                    value: value,
                    title: readonly ? '{% trans "Quantity cannot be adjusted for serialized stock" %}' : '{% trans "Specify stock quantity" %}',
                    required: true,
                },
                {
                    hideLabels: true,
                }
            );
        }

        var buttons = `<div class='btn-group float-right' role='group'>`;

        buttons += makeIconButton(
            'fa-times icon-red',
            'button-stock-item-remove',
            pk,
            '{% trans "Remove stock item" %}',
        );

        buttons += `</div>`;

        html += `
        <tr id='stock_item_${pk}' class='stock-item-row'>
            <td id='part_${pk}'>${thumb} ${item.part_detail.full_name}</td>
            <td id='stock_${pk}'>${quantity}${status}</td>
            <td id='location_${pk}'>${location}</td>
            <td id='action_${pk}'>
                <div id='div_id_${pk}'>
                    ${actionInput}
                    <div id='errors-${pk}'></div>
                </div>
            </td>
            <td id='buttons_${pk}'>${buttons}</td>
        </tr>`;

        itemCount += 1;
    }

    if (itemCount == 0) {
        showAlertDialog(
            '{% trans "Select Stock Items" %}',
            '{% trans "You must select at least one available stock item" %}',
        );

        return;
    }

    html += `</tbody></table>`;

    var extraFields = {};

    if (specifyLocation) {
        extraFields.location = {};
    }

    if (action != 'delete') {
        extraFields.notes = {};
    }

    constructForm(url, {
        method: 'POST',
        fields: extraFields,
        preFormContent: html,
        confirm: true,
        confirmMessage: '{% trans "Confirm stock adjustment" %}',
        title: formTitle,
        afterRender: function(fields, opts) {
            // Add button callbacks to remove rows
            $(opts.modal).find('.button-stock-item-remove').click(function() {
                var pk = $(this).attr('pk');

                $(opts.modal).find(`#stock_item_${pk}`).remove();
            });

            // Initialize "location" field
            if (specifyLocation) {
                initializeRelatedField(
                    {
                        name: 'location',
                        type: 'related field',
                        model: 'stocklocation',
                        required: true,
                    },
                    null,
                    opts
                );
            }
        },
        onSubmit: function(fields, opts) {

            // Extract data elements from the form
            var data = {
                items: [],
            };

            if (action != 'delete') {
                data.notes = getFormFieldValue('notes', {}, opts);
            }

            if (specifyLocation) {
                data.location = getFormFieldValue('location', {}, opts);
            }

            var item_pk_values = [];

            items.forEach(function(item) {
                var pk = item.pk;

                // Does the row exist in the form?
                var row = $(opts.modal).find(`#stock_item_${pk}`);

                if (row.exists()) {

                    item_pk_values.push(pk);

                    var quantity = getFormFieldValue(`items_quantity_${pk}`, {}, opts);

                    data.items.push({
                        pk: pk,
                        quantity: quantity,
                    });
                }
            });

            // Delete action is handled differently
            if (action == 'delete') {

                inventreeMultiDelete(
                    '{% url "api-stock-list" %}',
                    items,
                    {
                        modal: opts.modal,
                        success: options.success,
                    }
                );

                return;
            }

            opts.nested = {
                'items': item_pk_values,
            };

            inventreePut(
                url,
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


function removeStockRow(e) {
    // Remove a selected row from a stock modal form

    e = e || window.event;
    var src = e.target || e.srcElement;

    var row = $(src).attr('row');

    $('#' + row).remove();
}


function passFailBadge(result) {

    if (result) {
        return `<span class='badge badge-right rounded-pill bg-success'>{% trans "PASS" %}</span>`;
    } else {
        return `<span class='badge badge-right rounded-pill bg-danger'>{% trans "FAIL" %}</span>`;
    }
}

function noResultBadge() {
    return `<span class='badge badge-right rounded-pill bg-info'>{% trans "NO RESULT" %}</span>`;
}

function formatDate(row) {
    // Function for formatting date field
    var html = row.date;

    if (row.user_detail) {
        html += `<span class='badge badge-right rounded-pill bg-secondary'>${row.user_detail.username}</span>`;
    }

    return html;
}

/*
 * Load StockItemTestResult table
 */
function loadStockTestResultsTable(table, options) {

    // Setup filters for the table
    var filterTarget = options.filterTarget || '#filter-list-stocktests';

    var filterKey = options.filterKey || options.name || 'stocktests';

    var filters = loadTableFilters(filterKey);

    var params = {
        part: options.part,
    };

    var original = {};

    for (var k in params) {
        original[k] = params[k];
        filters[k] = params[k];
    }

    setupFilterList(filterKey, table, filterTarget);

    function makeButtons(row, grouped) {

        // Helper function for rendering buttons

        var html = `<div class='btn-group float-right' role='group'>`;

        if (row.requires_attachment == false && row.requires_value == false && !row.result) {
            // Enable a "quick tick" option for this test result
            html += makeIconButton('fa-check-circle icon-green', 'button-test-tick', row.test_name, '{% trans "Pass test" %}');
        }

        html += makeIconButton('fa-plus icon-green', 'button-test-add', row.test_name, '{% trans "Add test result" %}');

        if (!grouped && row.result != null) {
            var pk = row.pk;
            html += makeIconButton('fa-edit icon-blue', 'button-test-edit', pk, '{% trans "Edit test result" %}');
            html += makeIconButton('fa-trash-alt icon-red', 'button-test-delete', pk, '{% trans "Delete test result" %}');
        }

        html += '</div>';

        return html;
    }

    var parent_node = 'parent node';

    table.inventreeTable({
        url: '{% url "api-part-test-template-list" %}',
        method: 'get',
        name: 'testresult',
        treeEnable: true,
        rootParentId: parent_node,
        parentIdField: 'parent',
        idField: 'pk',
        uniqueId: 'pk',
        treeShowField: 'test_name',
        formatNoMatches: function() {
            return '{% trans "No test results found" %}';
        },
        queryParams: filters,
        original: original,
        onPostBody: function() {
            table.treegrid({
                treeColumn: 0,
            });
            table.treegrid('collapseAll');
        },
        columns: [
            {
                field: 'pk',
                title: 'ID',
                visible: false,
                switchable: false,
            },
            {
                field: 'test_name',
                title: '{% trans "Test Name" %}',
                sortable: true,
                formatter: function(value, row) {
                    var html = value;

                    if (row.required) {
                        html = `<b>${value}</b>`;
                    }

                    if (row.result == null) {
                        html += noResultBadge();
                    } else {
                        html += passFailBadge(row.result);
                    }

                    return html;
                }
            },
            {
                field: 'value',
                title: '{% trans "Value" %}',
                formatter: function(value, row) {
                    var html = value;

                    if (row.attachment) {
                        html += `<a href='${row.attachment}'><span class='fas fa-file-alt float-right'></span></a>`;
                    }

                    return html;
                }
            },
            {
                field: 'notes',
                title: '{% trans "Notes" %}',
            },
            {
                field: 'date',
                title: '{% trans "Test Date" %}',
                sortable: true,
                formatter: function(value, row) {
                    return formatDate(row);
                },
            },
            {
                field: 'buttons',
                formatter: function(value, row) {
                    return makeButtons(row, false);
                }
            }
        ],
        onLoadSuccess: function(tableData) {

            // Set "parent" for each existing row
            tableData.forEach(function(item, idx) {
                tableData[idx].parent = parent_node;
            });

            // Once the test template data are loaded, query for test results

            var filters = loadTableFilters(filterKey);

            var query_params = {
                stock_item: options.stock_item,
                user_detail: true,
                attachment_detail: true,
                ordering: '-date',
            };

            if ('result' in filters) {
                query_params.result = filters.result;
            }

            if ('include_installed' in filters) {
                query_params.include_installed = filters.include_installed;
            }

            inventreeGet(
                '{% url "api-stock-test-result-list" %}',
                query_params,
                {
                    success: function(data) {
                        // Iterate through the returned test data
                        data.forEach(function(item) {

                            var match = false;
                            var override = false;

                            // Extract the simplified test key
                            var key = item.key;

                            // Attempt to associate this result with an existing test
                            for (var idx = 0; idx < tableData.length; idx++) {

                                var row = tableData[idx];

                                if (key == row.key) {

                                    item.test_name = row.test_name;
                                    item.required = row.required;

                                    if (row.result == null) {
                                        item.parent = parent_node;
                                        tableData[idx] = item;
                                        override = true;
                                    } else {
                                        item.parent = row.pk;
                                    }

                                    match = true;

                                    break;
                                }
                            }

                            // No match could be found
                            if (!match) {
                                item.test_name = item.test;
                                item.parent = parent_node;
                            }

                            if (!override) {
                                tableData.push(item);
                            }

                        });

                        // Push data back into the table
                        table.bootstrapTable('load', tableData);
                    }
                }
            );
        }
    });

    /* Register button callbacks */

    function reloadTestTable(response) {
        $(table).bootstrapTable('refresh');
    }

    // "tick" a test result
    $(table).on('click', '.button-test-tick', function() {
        var button = $(this);

        var test_name = button.attr('pk');

        inventreePut(
            '{% url "api-stock-test-result-list" %}',
            {
                test: test_name,
                result: true,
                stock_item: options.stock_item,
            },
            {
                method: 'POST',
                success: reloadTestTable,
            }
        );
    });

    // Add a test result
    $(table).on('click', '.button-test-add', function() {
        var button = $(this);

        var test_name = button.attr('pk');

        constructForm('{% url "api-stock-test-result-list" %}', {
            method: 'POST',
            fields: {
                test: {
                    value: test_name,
                },
                result: {},
                value: {},
                attachment: {},
                notes: {},
                stock_item: {
                    value: options.stock_item,
                    hidden: true,
                }
            },
            title: '{% trans "Add Test Result" %}',
            onSuccess: reloadTestTable,
        });
    });

    // Edit a test result
    $(table).on('click', '.button-test-edit', function() {
        var button = $(this);

        var pk = button.attr('pk');

        var url = `/api/stock/test/${pk}/`;

        constructForm(url, {
            fields: {
                test: {},
                result: {},
                value: {},
                attachment: {},
                notes: {},
            },
            title: '{% trans "Edit Test Result" %}',
            onSuccess: reloadTestTable,
        });
    });

    // Delete a test result
    $(table).on('click', '.button-test-delete', function() {
        var button = $(this);

        var pk = button.attr('pk');

        var url = `/api/stock/test/${pk}/`;

        var row = $(table).bootstrapTable('getRowByUniqueId', pk);

        var html = `
        <div class='alert alert-block alert-danger'>
        <strong>{% trans "Delete test result" %}:</strong> ${row.test_name || row.test || row.key}
        </div>`;

        constructForm(url, {
            method: 'DELETE',
            title: '{% trans "Delete Test Result" %}',
            onSuccess: reloadTestTable,
            preFormContent: html,
        });
    });
}


function locationDetail(row, showLink=true) {
    /*
     * Function to display a "location" of a StockItem.
     *
     * Complicating factors: A StockItem may not actually *be* in a location!
     * - Could be at a customer
     * - Could be installed in another stock item
     * - Could be assigned to a sales order
     * - Could be currently in production!
     *
     * So, instead of being naive, we'll check!
     */

    // Display text
    var text = '';

    // URL (optional)
    var url = '';

    if (row.is_building && row.build) {
        // StockItem is currently being built!
        text = '{% trans "In production" %}';
        url = `/build/${row.build}/`;
    } else if (row.belongs_to) {
        // StockItem is installed inside a different StockItem
        text = `{% trans "Installed in Stock Item" %} ${row.belongs_to}`;
        url = `/stock/item/${row.belongs_to}/?display=installed-items`;
    } else if (row.customer) {
        // StockItem has been assigned to a customer
        text = '{% trans "Shipped to customer" %}';
        url = `/company/${row.customer}/?display=assigned-stock`;
    } else if (row.sales_order) {
        // StockItem has been assigned to a sales order
        text = '{% trans "Assigned to Sales Order" %}';
        url = `/order/sales-order/${row.sales_order}/`;
    } else if (row.location && row.location_detail) {
        text = row.location_detail.pathstring;
        url = `/stock/location/${row.location}/`;
    } else {
        text = '<i>{% trans "No stock location set" %}</i>';
        url = '';
    }

    if (showLink && url) {
        return renderLink(text, url);
    } else {
        return text;
    }
}


function loadStockTable(table, options) {
    /* Load data into a stock table with adjustable options.
     * Fetches data (via AJAX) and loads into a bootstrap table.
     * Also links in default button callbacks.
     *
     * Options:
     *  url - URL for the stock query
     *  params - query params for augmenting stock data request
     *  groupByField - Column for grouping stock items
     *  buttons - Which buttons to link to stock selection callbacks
     *  filterList - <ul> element where filters are displayed
     *  disableFilters: If true, disable custom filters
     */

    // List of user-params which override the default filters

    options.params['location_detail'] = true;
    options.params['part_detail'] = true;

    var params = options.params || {};

    var filterTarget = options.filterTarget || '#filter-list-stock';

    var filters = {};

    var filterKey = options.filterKey || options.name || 'stock';

    if (!options.disableFilters) {
        filters = loadTableFilters(filterKey);
    }

    var original = {};

    for (var k in params) {
        original[k] = params[k];
    }

    setupFilterList(filterKey, table, filterTarget, {download: true});

    // Override the default values, or add new ones
    for (var key in params) {
        filters[key] = params[key];
    }

    var grouping = true;

    if ('grouping' in options) {
        grouping = options.grouping;
    }

    var col = null;

    // Explicitly disable part grouping functionality
    // Might be able to add this in later on,
    // but there is a bug which makes this crash if paginating on the server side.
    // Ref: https://github.com/wenzhixin/bootstrap-table/issues/3250
    // eslint-disable-next-line no-unused-vars
    grouping = false;

    var columns = [
        {
            checkbox: true,
            title: '{% trans "Select" %}',
            searchable: false,
            switchable: false,
        },
        {
            field: 'pk',
            title: 'ID',
            visible: false,
            switchable: false,
        }
    ];

    col = {
        field: 'part_detail.full_name',
        title: '{% trans "Part" %}',
        sortName: 'part__name',
        visible: params['part_detail'],
        switchable: params['part_detail'],
        formatter: function(value, row) {

            var url = `/stock/item/${row.pk}/`;
            var thumb = row.part_detail.thumbnail;
            var name = row.part_detail.full_name;

            var html = imageHoverIcon(thumb) + renderLink(name, url);

            html += makePartIcons(row.part_detail);

            return html;
        }
    };

    if (!options.params.ordering) {
        col['sortable'] = true;
    }

    columns.push(col);

    col = {
        field: 'part_detail.IPN',
        title: '{% trans "IPN" %}',
        sortName: 'part__IPN',
        visible: params['part_detail'],
        switchable: params['part_detail'],
        formatter: function(value, row) {
            return row.part_detail.IPN;
        },
    };

    if (!options.params.ordering) {
        col['sortable'] = true;
    }

    columns.push(col);

    columns.push({
        field: 'part_detail.description',
        title: '{% trans "Description" %}',
        visible: params['part_detail'],
        switchable: params['part_detail'],
        formatter: function(value, row) {
            return row.part_detail.description;
        }
    });

    col = {
        field: 'quantity',
        sortName: 'stock',
        title: '{% trans "Stock" %}',
        sortable: true,
        formatter: function(value, row) {

            var val = '';

            var available = Math.max(0, (row.quantity || 0) - (row.allocated || 0));

            if (row.serial && row.quantity == 1) {
                // If there is a single unit with a serial number, use the serial number
                val = '# ' + row.serial;
            } else if (row.quantity != available) {
                // Some quantity is available, show available *and* quantity
                var ava = +parseFloat(available).toFixed(5);
                var tot = +parseFloat(row.quantity).toFixed(5);

                val = `${ava} / ${tot}`;
            } else {
                // Format floating point numbers with this one weird trick
                val = +parseFloat(value).toFixed(5);
            }

            var html = renderLink(val, `/stock/item/${row.pk}/`);

            if (row.is_building) {
                html += makeIconBadge('fa-tools', '{% trans "Stock item is in production" %}');
            }

            if (row.sales_order) {
                // Stock item has been assigned to a sales order
                html += makeIconBadge('fa-truck', '{% trans "Stock item assigned to sales order" %}');
            } else if (row.customer) {
                // StockItem has been assigned to a customer
                html += makeIconBadge('fa-user', '{% trans "Stock item assigned to customer" %}');
            } else if (row.allocated) {
                if (row.serial != null && row.quantity == 1) {
                    html += makeIconBadge('fa-bookmark icon-yellow', '{% trans "Serialized stock item has been allocated" %}');
                } else if (row.allocated >= row.quantity) {
                    html += makeIconBadge('fa-bookmark icon-yellow', '{% trans "Stock item has been fully allocated" %}');
                } else {
                    html += makeIconBadge('fa-bookmark', '{% trans "Stock item has been partially allocated" %}');
                }
            } else if (row.belongs_to) {
                html += makeIconBadge('fa-box', '{% trans "Stock item has been installed in another item" %}');
            }

            if (row.expired) {
                html += makeIconBadge('fa-calendar-times icon-red', '{% trans "Stock item has expired" %}');
            } else if (row.stale) {
                html += makeIconBadge('fa-stopwatch', '{% trans "Stock item will expire soon" %}');
            }

            // Special stock status codes

            // REJECTED
            if (row.status == {{ StockStatus.REJECTED }}) {
                html += makeIconBadge('fa-times-circle icon-red', '{% trans "Stock item has been rejected" %}');
            } else if (row.status == {{ StockStatus.LOST }}) {
                html += makeIconBadge('fa-question-circle', '{% trans "Stock item is lost" %}');
            } else if (row.status == {{ StockStatus.DESTROYED }}) {
                html += makeIconBadge('fa-skull-crossbones', '{% trans "Stock item is destroyed" %}');
            }

            if (row.quantity <= 0) {
                html += `<span class='badge badge-right rounded-pill bg-danger'>{% trans "Depleted" %}</span>`;
            }

            return html;
        }
    };

    columns.push(col);

    col = {
        field: 'status',
        title: '{% trans "Status" %}',
        formatter: function(value) {
            return stockStatusDisplay(value);
        },
    };

    if (!options.params.ordering) {
        col['sortable'] = true;
    }

    columns.push(col);

    col = {
        field: 'batch',
        title: '{% trans "Batch" %}',
    };

    if (!options.params.ordering) {
        col['sortable'] = true;
    }

    columns.push(col);

    col = {
        field: 'location_detail.pathstring',
        title: '{% trans "Location" %}',
        sortName: 'location',
        formatter: function(value, row) {
            return locationDetail(row);
        }
    };

    if (!options.params.ordering) {
        col['sortable'] = true;
    }

    columns.push(col);

    col = {
        field: 'stocktake_date',
        title: '{% trans "Stocktake" %}',
        formatter: function(value) {
            return renderDate(value);
        }
    };

    if (!options.params.ordering) {
        col['sortable'] = true;
    }

    columns.push(col);

    col = {
        field: 'expiry_date',
        title: '{% trans "Expiry Date" %}',
        visible: global_settings.STOCK_ENABLE_EXPIRY,
        switchable: global_settings.STOCK_ENABLE_EXPIRY,
        formatter: function(value) {
            return renderDate(value);
        }
    };

    if (!options.params.ordering) {
        col['sortable'] = true;
    }

    columns.push(col);

    col = {
        field: 'updated',
        title: '{% trans "Last Updated" %}',
        formatter: function(value) {
            return renderDate(value);
        }
    };

    if (!options.params.ordering) {
        col['sortable'] = true;
    }

    columns.push(col);

    columns.push({
        field: 'purchase_order',
        title: '{% trans "Purchase Order" %}',
        formatter: function(value, row) {
            if (!value) {
                return '-';
            }

            var link = `/order/purchase-order/${row.purchase_order}/`;
            var text = `${row.purchase_order}`;

            if (row.purchase_order_reference) {

                var prefix = global_settings.PURCHASEORDER_REFERENCE_PREFIX;

                text = prefix + row.purchase_order_reference;
            }

            return renderLink(text, link);
        }
    });

    col = {

        field: 'supplier_part',
        title: '{% trans "Supplier Part" %}',
        visible: params['supplier_part_detail'] || false,
        switchable: params['supplier_part_detail'] || false,
        formatter: function(value, row) {
            if (!value) {
                return '-';
            }

            var link = `/supplier-part/${row.supplier_part}/?display=part-stock`;

            var text = '';

            if (row.supplier_part_detail) {
                text = `${row.supplier_part_detail.SKU}`;
            } else {
                text = `<i>{% trans "Supplier part not specified" %}</i>`;
            }

            return renderLink(text, link);
        }
    };

    if (!options.params.ordering) {
        col.sortable = true;
        col.sortName = 'SKU';
    }

    columns.push(col);

    col = {
        field: 'purchase_price_string',
        title: '{% trans "Purchase Price" %}',
    };

    if (!options.params.ordering) {
        col.sortable = true;
        col.sortName = 'purchase_price';
    }

    columns.push(col);

    columns.push({
        field: 'packaging',
        title: '{% trans "Packaging" %}',
    },
    {
        field: 'notes',
        title: '{% trans "Notes" %}',
    });

    table.inventreeTable({
        method: 'get',
        formatNoMatches: function() {
            return '{% trans "No stock items matching query" %}';
        },
        url: options.url || '{% url "api-stock-list" %}',
        queryParams: filters,
        sidePagination: 'server',
        name: 'stock',
        original: original,
        showColumns: true,
        columns: columns,
    });

    var buttons = [
        '#stock-print-options',
        '#stock-options',
    ];

    if (global_settings.BARCODE_ENABLE) {
        buttons.push('#stock-barcode-options');
    }

    linkButtonsToSelection(
        table,
        buttons,
    );

    function stockAdjustment(action) {
        var items = getTableData(table);

        adjustStock(action, items, {
            success: function() {
                $(table).bootstrapTable('refresh');
            }
        });
    }

    // Automatically link button callbacks

    $('#multi-item-print-label').click(function() {
        var selections = getTableData(table);

        var items = [];

        selections.forEach(function(item) {
            items.push(item.pk);
        });

        printStockItemLabels(items);
    });

    $('#multi-item-print-test-report').click(function() {
        var selections = getTableData(table);

        var items = [];

        selections.forEach(function(item) {
            items.push(item.pk);
        });

        printTestReports(items);
    });

    if (global_settings.BARCODE_ENABLE) {
        $('#multi-item-barcode-scan-into-location').click(function() {
            var selections = getTableData(table);

            var items = [];

            selections.forEach(function(item) {
                items.push(item);
            });

            scanItemsIntoLocation(items);
        });
    }

    $('#multi-item-stocktake').click(function() {
        stockAdjustment('count');
    });

    $('#multi-item-remove').click(function() {
        stockAdjustment('take');
    });

    $('#multi-item-add').click(function() {
        stockAdjustment('add');
    });

    $('#multi-item-move').click(function() {
        stockAdjustment('move');
    });

    $('#multi-item-merge').click(function() {
        var items = getTableData(table);

        mergeStockItems(items, {
            success: function(response) {
                $(table).bootstrapTable('refresh');

                showMessage('{% trans "Merged stock items" %}', {
                    style: 'success',
                });
            }
        });
    });

    $('#multi-item-assign').click(function() {

        var items = getTableData(table);

        assignStockToCustomer(items, {
            success: function() {
                $(table).bootstrapTable('refresh');
            }
        });
    });

    $('#multi-item-order').click(function() {

        var selections = getTableData(table);

        var parts = [];

        selections.forEach(function(item) {
            var part = item.part_detail;

            if (part) {
                parts.push(part);
            }
        });

        orderParts(parts, {});
    });

    $('#multi-item-set-status').click(function() {
        // Select and set the STATUS field for selected stock items
        var selections = getTableData(table);

        // Select stock status
        var modal = '#modal-form';

        var status_list = makeOptionsList(
            stockStatusCodes(),
            function(item) {
                return item.text;
            },
            function(item) {
                return item.key;
            }
        );

        // Add an empty option at the start of the list
        status_list.unshift('<option value="">---------</option>');

        // Construct form
        var html = `
        <form method='post' action='' class='js-modal-form' enctype='multipart/form-data'>
            <div class='form-group'>
                <label class='control-label requiredField' for='id_status'>
                {% trans "Stock Status" %}
                </label>
                <div class='controls'>
                    <select id='id_status' class='select form-control' name='label'>
                        ${status_list}
                    </select>
                </div>
            </div>
        </form>`;

        openModal({
            modal: modal,
        });

        modalEnable(modal, true);
        modalSetTitle(modal, '{% trans "Set Stock Status" %}');
        modalSetContent(modal, html);

        attachSelect(modal);

        modalSubmit(modal, function() {
            var label = $(modal).find('#id_status');

            var status_code = label.val();

            closeModal(modal);

            if (!status_code) {
                showAlertDialog(
                    '{% trans "Select Status Code" %}',
                    '{% trans "Status code must be selected" %}'
                );

                return;
            }

            var requests = [];

            selections.forEach(function(item) {
                var url = `/api/stock/${item.pk}/`;

                requests.push(
                    inventreePut(
                        url,
                        {
                            status: status_code,
                        },
                        {
                            method: 'PATCH',
                            success: function() {
                            }
                        }
                    )
                );
            });

            $.when.apply($, requests).done(function() {
                $(table).bootstrapTable('refresh');
            });
        });
    });

    $('#multi-item-delete').click(function() {
        var selections = getTableData(table);

        var stock = [];

        selections.forEach(function(item) {
            stock.push(item.pk);
        });

        stockAdjustment('delete');
    });
}


/*
 * Display a table of stock locations
 */
function loadStockLocationTable(table, options) {

    var params = options.params || {};

    var filterListElement = options.filterList || '#filter-list-location';

    var tree_view = options.allowTreeView && inventreeLoad('location-tree-view') == 1;

    if (tree_view) {
        params.cascade = true;
    }

    var filters = {};

    var filterKey = options.filterKey || options.name || 'location';

    if (!options.disableFilters) {
        filters = loadTableFilters(filterKey);
    }

    var original = {};

    for (var k in params) {
        original[k] = params[k];
    }

    setupFilterList(filterKey, table, filterListElement);

    for (var key in params) {
        filters[key] = params[key];
    }

    table.inventreeTable({
        treeEnable: tree_view,
        rootParentId: tree_view ? options.params.parent : null,
        uniqueId: 'pk',
        idField: 'pk',
        treeShowField: 'name',
        parentIdField: tree_view ? 'parent' : null,
        disablePagination: tree_view,
        sidePagination: tree_view ? 'client' : 'server',
        serverSort: !tree_view,
        search: !tree_view,
        method: 'get',
        url: options.url || '{% url "api-location-list" %}',
        queryParams: filters,
        name: 'location',
        original: original,
        showColumns: true,
        onPostBody: function() {

            if (options.allowTreeView) {

                tree_view = inventreeLoad('location-tree-view') == 1;

                if (tree_view) {

                    $('#view-location-list').removeClass('btn-secondary').addClass('btn-outline-secondary');
                    $('#view-location-tree').removeClass('btn-outline-secondary').addClass('btn-secondary');

                    table.treegrid({
                        treeColumn: 1,
                        onChange: function() {
                            table.bootstrapTable('resetView');
                        },
                        onExpand: function() {

                        }
                    });
                } else {
                    $('#view-location-tree').removeClass('btn-secondary').addClass('btn-outline-secondary');
                    $('#view-location-list').removeClass('btn-outline-secondary').addClass('btn-secondary');
                }
            }
        },
        buttons: options.allowTreeView ? [
            {
                icon: 'fas fa-bars',
                attributes: {
                    title: '{% trans "Display as list" %}',
                    id: 'view-location-list',
                },
                event: () => {
                    inventreeSave('location-tree-view', 0);
                    table.bootstrapTable(
                        'refreshOptions',
                        {
                            treeEnable: false,
                            serverSort: true,
                            search: true,
                            pagination: true,
                        }
                    );
                }
            },
            {
                icon: 'fas fa-sitemap',
                attributes: {
                    title: '{% trans "Display as tree" %}',
                    id: 'view-location-tree',
                },
                event: () => {
                    inventreeSave('location-tree-view', 1);
                    table.bootstrapTable(
                        'refreshOptions',
                        {
                            treeEnable: true,
                            serverSort: false,
                            search: false,
                            pagination: false,
                        }
                    );
                }
            }
        ] : [],
        columns: [
            {
                checkbox: true,
                title: '{% trans "Select" %}',
                searchable: false,
                switchable: false,
            },
            {
                field: 'name',
                title: '{% trans "Name" %}',
                switchable: true,
                sortable: true,
                formatter: function(value, row) {
                    return renderLink(
                        value,
                        `/stock/location/${row.pk}/`
                    );
                },
            },
            {
                field: 'description',
                title: '{% trans "Description" %}',
                switchable: true,
                sortable: false,
            },
            {
                field: 'pathstring',
                title: '{% trans "Path" %}',
                switchable: true,
                sortable: false,
            },
            {
                field: 'items',
                title: '{% trans "Stock Items" %}',
                switchable: true,
                sortable: false,
                sortName: 'item_count',
            }
        ]
    });
}

function loadStockTrackingTable(table, options) {

    var cols = [];

    var filterTarget = '#filter-list-stocktracking';

    var filterKey = 'stocktracking';

    var filters = loadTableFilters(filterKey);

    var params = options.params;

    var original = {};

    for (var k in params) {
        original[k] = params[k];
        filters[k] = params[k];
    }

    setupFilterList(filterKey, table, filterTarget);

    // Date
    cols.push({
        field: 'date',
        title: '{% trans "Date" %}',
        sortable: true,
        formatter: function(value) {
            return renderDate(value, {showTime: true});
        }
    });

    // Stock transaction description
    cols.push({
        field: 'label',
        title: '{% trans "Description" %}',
        formatter: function(value, row) {
            var html = '<b>' + value + '</b>';

            if (row.notes) {
                html += '<br><i>' + row.notes + '</i>';
            }

            return html;
        }
    });

    // Stock transaction details
    cols.push({
        field: 'deltas',
        title: '{% trans "Details" %}',
        formatter: function(details, row) {
            var html = `<table class='table table-condensed' id='tracking-table-${row.pk}'>`;

            if (!details) {
                html += '</table>';
                return html;
            }

            // Part information
            if (details.part) {
                html += `<tr><th>{% trans "Part" %}</th><td>`;

                if (details.part_detail) {
                    html += renderLink(details.part_detail.full_name, `/part/${details.part}/`);
                } else {
                    html += `{% trans "Part information unavailable" %}`;
                }

                html += `</td></tr>`;
            }

            // Location information
            if (details.location) {

                html += `<tr><th>{% trans "Location" %}</th>`;

                html += '<td>';

                if (details.location_detail) {
                    // A valid location is provided

                    html += renderLink(
                        details.location_detail.pathstring,
                        details.location_detail.url,
                    );
                } else {
                    // An invalid location (may have been deleted?)
                    html += `<i>{% trans "Location no longer exists" %}</i>`;
                }

                html += '</td></tr>';
            }

            // Purchase Order Information
            if (details.purchaseorder) {

                html += `<tr><th>{% trans "Purchase Order" %}</td>`;

                html += '<td>';

                if (details.purchaseorder_detail) {
                    html += renderLink(
                        details.purchaseorder_detail.reference,
                        `/order/purchase-order/${details.purchaseorder}/`
                    );
                } else {
                    html += `<i>{% trans "Purchase order no longer exists" %}</i>`;
                }

                html += '</td></tr>';
            }

            // Customer information
            if (details.customer) {

                html += `<tr><th>{% trans "Customer" %}</td>`;

                html += '<td>';

                if (details.customer_detail) {
                    html += renderLink(
                        details.customer_detail.name,
                        details.customer_detail.url
                    );
                } else {
                    html += `<i>{% trans "Customer no longer exists" %}</i>`;
                }

                html += '</td></tr>';
            }

            // Stockitem information
            if (details.stockitem) {
                html += '<tr><th>{% trans "Stock Item" %}</td>';

                html += '<td>';

                if (details.stockitem_detail) {
                    html += renderLink(
                        details.stockitem,
                        `/stock/item/${details.stockitem}/`
                    );
                } else {
                    html += `<i>{% trans "Stock item no longer exists" %}</i>`;
                }

                html += '</td></tr>';
            }

            // Status information
            if (details.status) {
                html += `<tr><th>{% trans "Status" %}</td>`;

                html += '<td>';
                html += stockStatusDisplay(
                    details.status,
                    {
                        classes: 'float-right',
                    }
                );
                html += '</td></tr>';

            }

            // Quantity information
            if (details.added) {
                html += '<tr><th>{% trans "Added" %}</th>';

                html += `<td>${details.added}</td>`;

                html += '</tr>';
            }

            if (details.removed) {
                html += '<tr><th>{% trans "Removed" %}</th>';

                html += `<td>${details.removed}</td>`;

                html += '</tr>';
            }

            if (details.quantity) {
                html += '<tr><th>{% trans "Quantity" %}</th>';

                html += `<td>${details.quantity}</td>`;

                html += '</tr>';
            }

            html += '</table>';

            return html;
        }
    });

    cols.push({
        field: 'user',
        title: '{% trans "User" %}',
        formatter: function(value, row) {
            if (value) {
                // TODO - Format the user's first and last names
                return row.user_detail.username;
            } else {
                return `<i>{% trans "No user information" %}</i>`;
            }
        }
    });

    table.inventreeTable({
        method: 'get',
        queryParams: filters,
        original: original,
        columns: cols,
        url: options.url,
    });

    if (options.buttons) {
        linkButtonsToSelection(table, options.buttons);
    }

    table.on('click', '.btn-entry-edit', function() {
        var button = $(this);

        launchModalForm(button.attr('url'), {
            reload: true,
        });
    });

    table.on('click', '.btn-entry-delete', function() {
        var button = $(this);

        launchModalForm(button.attr('url'), {
            reload: true,
        });
    });
}


function loadInstalledInTable(table, options) {
    /*
    * Display a table showing the stock items which are installed in this stock item.
    */

    table.inventreeTable({
        url: '{% url "api-stock-list" %}',
        queryParams: {
            installed_in: options.stock_item,
            part_detail: true,
        },
        formatNoMatches: function() {
            return '{% trans "No installed items" %}';
        },
        columns: [
            {
                field: 'part',
                title: '{% trans "Part" %}',
                formatter: function(value, row) {
                    var html = '';

                    html += imageHoverIcon(row.part_detail.thumbnail);
                    html += renderLink(row.part_detail.full_name, `/stock/item/${row.pk}/`);

                    return html;
                }
            },
            {
                field: 'quantity',
                title: '{% trans "Quantity" %}',
                formatter: function(value, row) {

                    var html = '';

                    if (row.serial && row.quantity == 1) {
                        html += `{% trans "Serial" %}: ${row.serial}`;
                    } else {
                        html += `${row.quantity}`;
                    }

                    return renderLink(html, `/stock/item/${row.pk}/`);
                }
            },
            {
                field: 'status',
                title: '{% trans "Status" %}',
                formatter: function(value) {
                    return stockStatusDisplay(value);
                }
            },
            {
                field: 'batch',
                title: '{% trans "Batch" %}',
            },
            {
                field: 'buttons',
                title: '',
                switchable: false,
                formatter: function(value, row) {
                    var pk = row.pk;
                    var html = '';

                    html += `<div class='btn-group float-right' role='group'>`;
                    html += makeIconButton('fa-unlink', 'button-uninstall', pk, '{% trans "Uninstall Stock Item" %}');
                    html += `</div>`;

                    return html;
                }
            }
        ],
        onPostBody: function() {
            // Assign callbacks to the buttons
            table.find('.button-uninstall').click(function() {
                var pk = $(this).attr('pk');

                uninstallStockItem(
                    pk,
                    {
                        onSuccess: function(response) {
                            table.bootstrapTable('refresh');
                        }
                    }
                );
            });
        }
    });
}


/*
 * Launch a dialog to uninstall a stock item from another stock item
*/
function uninstallStockItem(installed_item_id, options={}) {

    constructForm(
        `/api/stock/${installed_item_id}/uninstall/`,
        {
            confirm: true,
            method: 'POST',
            title: '{% trans "Uninstall Stock Item" %}',
            fields: {
                location: {
                    icon: 'fa-sitemap',
                },
                note: {},
            },
            preFormContent: function(opts) {
                var html = '';

                if (installed_item_id == null) {
                    html += `
                    <div class='alert alert-block alert-info'>
                    {% trans "Select stock item to uninstall" %}
                    </div>`;
                }

                return html;
            },
            onSuccess: function(response) {
                handleFormSuccess(response, options);
            }
        }
    );
}


/*
 * Launch a dialog to install a stock item into another stock item
 */
function installStockItem(stock_item_id, part_id, options={}) {

    var html = `
    <div class='alert alert-block alert-info'>
        <strong>{% trans "Install another stock item into this item" %}</strong><br>
        {% trans "Stock items can only be installed if they meet the following criteria" %}:<br>
        <ul>
            <li>{% trans "The Stock Item links to a Part which is the BOM for this Stock Item" %}</li>
            <li>{% trans "The Stock Item is currently available in stock" %}</li>
            <li>{% trans "The Stock Item is not already installed in another item" %}</li>
            <li>{% trans "The Stock Item is tracked by either a batch code or serial number" %}</li>
        </ul>
    </div>`;

    constructForm(
        `/api/stock/${stock_item_id}/install/`,
        {
            method: 'POST',
            fields: {
                part: {
                    type: 'related field',
                    required: 'true',
                    label: '{% trans "Part" %}',
                    help_text: '{% trans "Select part to install" %}',
                    model: 'part',
                    api_url: '{% url "api-part-list" %}',
                    auto_fill: true,
                    filters: {
                        trackable: true,
                        in_bom_for: part_id,
                    }
                },
                stock_item: {
                    filters: {
                        part_detail: true,
                        in_stock: true,
                        tracked: true,
                    },
                    adjustFilters: function(filters, opts) {
                        var part = getFormFieldValue('part', {}, opts);

                        if (part) {
                            filters.part = part;
                        }

                        return filters;
                    }
                }
            },
            confirm: true,
            title: '{% trans "Install Stock Item" %}',
            preFormContent: html,
            onSuccess: function(response) {
                if (options.onSuccess) {
                    options.onSuccess(response);
                }
            }
        }
    );
}
