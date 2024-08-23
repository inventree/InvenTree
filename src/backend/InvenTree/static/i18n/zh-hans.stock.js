



/* globals
    addCachedAlert,
    addTableFilter,
    baseCurrency,
    calculateTotalPrice,
    clearFormInput,
    constructField,
    constructForm,
    constructFormBody,
    convertCurrency,
    disableFormInput,
    enableFormInput,
    formatCurrency,
    formatDecimal,
    formatPriceRange,
    getApiIconClass,
    getCurrencyConversionRates,
    getFormFieldElement,
    getFormFieldValue,
    getTableData,
    global_settings,
    handleFormErrors,
    handleFormSuccess,
    imageHoverIcon,
    initializeRelatedField,
    inventreeDelete,
    inventreeGet,
    inventreeLoad,
    inventreePut,
    inventreeSave,
    launchModalForm,
    loadTableFilters,
    makeDeleteButton,
    makeEditButton,
    makeIconBadge,
    makeIconButton,
    makeRemoveButton,
    moment,
    orderParts,
    partDetail,
    reloadTableFilters,
    removeTableFilter,
    renderClipboard,
    renderDate,
    renderLink,
    scanItemsIntoLocation,
    setFormInputPlaceholder,
    setupFilterList,
    shortenString,
    showAlertDialog,
    showAlertOrCache,
    showMessage,
    showModalSpinner,
    showApiError,
    stockCodes,
    stockStatusDisplay,
    thumbnailImage,
    updateFieldValue,
    withTitle,
    wrapButtons,
    yesNoLabel,
*/

/* exported
    assignStockToCustomer,
    createNewStockItem,
    createStockLocation,
    deleteStockItem,
    deleteStockLocation,
    duplicateStockItem,
    editStockItem,
    editStockLocation,
    filterTestStatisticsTableDateRange,
    findStockItemBySerialNumber,
    installStockItem,
    loadInstalledInTable,
    loadStockLocationTable,
    loadStockTable,
    loadStockTestResultsTable,
    loadStockTrackingTable,
    loadTableFilters,
    prepareTestStatisticsTable,
    mergeStockItems,
    removeStockRow,
    serializeStockItem,
    stockItemFields,
    stockLocationFields,
    stockLocationTypeFields,
    uninstallStockItem,
*/


/*
 * Launches a modal form to serialize a particular StockItem
 */

function serializeStockItem(pk, options={}) {

    var url = `/api/stock/${pk}/serialize/`;

    options.method = 'POST';
    options.title = '序列化库存项目';

    options.fields = {
        quantity: {},
        serial_numbers: {
            icon: 'fa-hashtag',
        },
        destination: {
            icon: 'fa-sitemap',
            filters: {
                structural: false,
            }
        },
        notes: {},
    };

    if (options.part) {
        // Work out the next available serial number
        inventreeGet(`/api/part/${options.part}/serial-numbers/`, {}, {
            success: function(data) {
                if (data.next) {
                    options.fields.serial_numbers.placeholder = `下一个可用序列号: ${data.next}`;
                } else if (data.latest) {
                    options.fields.serial_numbers.placeholder = `最新序列号: ${data.latest}`;
                }
            },
            async: false,
        });
    }

    options.confirm = true;
    options.confirmMessage = '确认库存序列化';

    constructForm(url, options);
}

function stockLocationTypeFields() {
    const fields = {
        name: {},
        description: {},
        icon: {
            help_text: `图标(可选) - 浏览所有可用图标 <a href="https://tabler.io/icons" target="_blank" rel="noopener noreferrer">Tabler Icons</a>.`,
            placeholder: 'ti:<icon-name>:<variant> (e.g. ti:alert-circle:filled)',
            icon: "fa-icons",
        },
    }

    return fields;
}


function stockLocationFields(options={}) {
    var fields = {
        parent: {
            help_text: '上级库存地点',
            required: false,
            tree_picker: {
                url: '/api/stock/location/tree/',
            },
        },
        name: {},
        description: {},
        owner: {},
        structural: {},
        external: {},
        location_type: {
            secondary: {
                title: '添加位置类型',
                fields: function() {
                    const fields = stockLocationTypeFields();

                    return fields;
                }
            },
        },
        custom_icon: {
            help_text: `图标(可选) - 浏览所有可用图标 <a href="https://tabler.io/icons" target="_blank" rel="noopener noreferrer">Tabler Icons</a>.`,
            placeholder: 'ti:<icon-name>:<variant> (e.g. ti:alert-circle:filled)',
            icon: "fa-icons",
        },
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

    options.title = '编辑库存地点';

    constructForm(url, options);
}


/*
 * Launch an API form to create a new stock location
 */
function createStockLocation(options={}) {

    var url = '/api/stock/location/';

    options.method = 'POST';
    options.fields = stockLocationFields(options);
    options.title = '添加库存地点';
    options.persist = true;
    options.persistMessage = '在此位置之后创建另一个位置';
    options.successMessage = '库存地点已创建';

    constructForm(url, options);
}


/*
 * Launch an API form to delete a StockLocation
 */
function deleteStockLocation(pk, options={}) {
    var url = `/api/stock/location/${pk}/`;

    var html = `
    <div class='alert alert-block alert-danger'>
    您确定要删除此库存位置吗？
    </div>
    `;

    var subChoices = [
        {
            value: 0,
            display_name: '移动到母库存位置',
        },
        {
            value: 1,
            display_name: '删除',
        }
    ];

    constructForm(url, {
        title: '删除库存地点',
        method: 'DELETE',
        fields: {
            'delete_stock_items': {
                label: '此库存位置的库存物品操作',
                choices: subChoices,
                type: 'choice'
            },
            'delete_sub_locations': {
                label: '针对子地点的行动',
                choices: subChoices,
                type: 'choice'
            },
        },
        preFormContent: html,
        onSuccess: function(response) {
            handleFormSuccess(response, options);
        }
    });
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
                                    placeholder = `下一个可用序列号: ${data.next}`;
                                } else if (data.latest) {
                                    placeholder = `最新序列号: ${data.latest}`;
                                }

                                setFormInputPlaceholder('serial_numbers', placeholder, opts);

                                if (global_settings.SERIAL_NUMBER_AUTOFILL) {
                                    if (data.next) {
                                        updateFieldValue('serial_numbers', `${data.next}+`, {}, opts);
                                    }
                                }
                            }
                        });

                    } else {
                        clearFormInput('serial_numbers', opts);
                        disableFormInput('serial_numbers', opts);

                        setFormInputPlaceholder('serial_numbers', '此零件无法序列化', opts);
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
        use_pack_size: {
            help_text: '将给定数量添加为包，而不是单个项目',
        },
        location: {
            icon: 'fa-sitemap',
            filters: {
                structural: false,
            },
            tree_picker: {
                url: '/api/stock/location/tree/',
            },
        },
        quantity: {
            help_text: '输入此库存项目的初始数量',
        },
        serial_numbers: {
            icon: 'fa-hashtag',
            type: 'string',
            label: '序號',
            help_text: '输入新库存的序列号(或留空)',
            required: false,
        },
        serial: {
            icon: 'fa-hashtag',
        },
        batch: {
            icon: 'fa-layer-group',
        },
        status: {},
        expiry_date: {
            icon: 'fa-calendar-alt',
        },
        purchase_price: {
            icon: 'fa-dollar-sign',
        },
        purchase_price_currency: {
            icon: 'fa-coins',
        },
        packaging: {
            icon: 'fa-box',
        },
        link: {
            icon: 'fa-link',
        },
        owner: {
            icon: 'fa-user',
        },
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

            showAlertOrCache('库存项重复', true, {style: 'success'});

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
            options.title = '复制库存项';

            constructForm('/api/stock/', options);
        }
    });
}


/*
 * Launch a modal form to delete a given StockItem
 */
function deleteStockItem(pk, options={}) {
    var url = `/api/stock/${pk}/`;

    var html = `
    <div class='alert alert-block alert-danger'>
    确定要删除此库存项吗?
    </div>`;

    constructForm(url, {
        method: 'DELETE',
        title: '删除库存项',
        preFormContent: html,
        onSuccess: function(response) {
            handleFormSuccess(response, options);
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

    options.title = '编辑库存项';

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

    var url = '/api/stock/';

    options.title = '新库存项目';
    options.method = 'POST';

    options.create = true;

    options.persist = true;
    options.persistMessage = '在此之后创建另一个项目';
    options.successMessage = '库存项已创建';

    options.fields = stockItemFields(options);
    options.groups = stockItemGroups(options);

    if (!options.onSuccess) {
        options.onSuccess = function(response) {
            // If a single stock item has been created, follow it!
            if (response.pk) {
                var url = `/stock/item/${response.pk}/`;

                addCachedAlert('新建库存项', {
                    icon: 'fas fa-boxes',
                });

                window.location.href = url;
            } else {

                // Multiple stock items have been created (i.e. serialized stock)
                var details = `
                <br>數量: ${response.quantity}
                <br>序號: ${response.serial_numbers}
                `;

                showMessage('创建了多个库存项目', {
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
        title: '查找序列号',
        fields: {
            serial: {
                label: '序列号',
                help_text: '输入序列号',
                placeholder: '输入序列号',
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
                            '输入序列号',
                        ]
                    }, fields, opts
                );
                return;
            }

            inventreeGet(
                '/api/stock/',
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
                                        '没有匹配的序列号',
                                    ]
                                }, fields, opts
                            );
                        } else if (response.length > 1) {
                            // Too many results!
                            handleFormErrors(
                                {
                                    'serial': [
                                        '找到多个匹配结果',
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


/**
 * Assign multiple stock items to a customer
 */
function assignStockToCustomer(items, options={}) {

    // Generate HTML content for the form
    var html = `
    <table class='table table-striped table-condensed' id='stock-assign-table'>
    <thead>
        <tr>
            <th>零件</th>
            <th>庫存品項</th>
            <th>地點</th>
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

        var status = stockStatusDisplay(item.status_custom_key, {classes: 'float-right'});

        var quantity = '';

        if (item.serial && item.quantity == 1) {
            quantity = `系列: ${item.serial}`;
        } else {
            quantity = `數量: ${item.quantity}`;
        }

        quantity += status;

        var location = locationDetail(item, false);

        var buttons = `<div class='btn-group' role='group'>`;

        buttons += makeRemoveButton(
            'button-stock-item-remove',
            pk,
            '移除行',
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

    constructForm('/api/stock/assign/', {
        method: 'POST',
        preFormContent: html,
        fields: {
            customer: {
                value: options.customer,
                filters: {
                    is_customer: true,
                },
            },
            notes: {
                icon: 'fa-sticky-note',
            },
        },
        confirm: true,
        confirmMessage: '确认库存分配',
        title: '将库存分配给客户',
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
                '/api/stock/assign/',
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
    <h5>警告：合并操作无法撤销</h5>
    <strong>合并库存项目时会丢失一些信息:</strong>
    <ul>
        <li>合并项目的库存交易历史记录将被删除</li>
        <li>合并项目的供应商零件信息将被删除</li>
    </ul>
    </div>
    `;

    html += `
    <table class='table table-striped table-condensed' id='stock-merge-table'>
    <thead>
        <tr>
            <th>零件</th>
            <th>庫存品項</th>
            <th>地點</th>
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
        let location_detail = locationDetail(item, false);

        var thumbnail = thumbnailImage(part.thumbnail || part.image);

        var quantity = '';

        if (item.serial && item.quantity == 1) {
            quantity = `系列: ${item.serial}`;
        } else {
            quantity = `數量: ${item.quantity}`;
        }

        quantity += stockStatusDisplay(item.status_custom_key, {classes: 'float-right'});

        let buttons = wrapButtons(
            makeIconButton(
                'fa-times icon-red',
                'button-stock-item-remove',
                pk,
                '移除行',
            )
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
            <td id='location_${pk}'>${location_detail}</td>
            <td id='buttons_${pk}'>${buttons}</td>
        </tr>
        `;
    }

    html += '</tbody></table>';

    var location = locations.length == 1 ? locations[0] : null;

    constructForm('/api/stock/merge/', {
        method: 'POST',
        preFormContent: html,
        fields: {
            location: {
                value: location,
                icon: 'fa-sitemap',
                filters: {
                    structural: false,
                },
                tree_picker: {
                    url: '/api/stock/location/tree/',
                },
            },
            notes: {
                icon: 'fa-sticky-note',
            },
            allow_mismatched_suppliers: {},
            allow_mismatched_status: {},
        },
        confirm: true,
        confirmMessage: '确认合并库存项',
        title: '合并库存项目',
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
                '/api/stock/merge/',
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

    let formTitle = 'Form Title Here';
    let actionTitle = null;

    const allowExtraFields = action == 'move';

    // API url
    var url = null;

    let specifyLocation = false;
    let allowSerializedStock = false;

    switch (action) {
    case 'move':
        formTitle = '转移库存';
        actionTitle = '移动';
        specifyLocation = true;
        allowSerializedStock = true;
        url = '/api/stock/transfer/';
        break;
    case 'count':
        formTitle = '库存计数';
        actionTitle = '计数';
        url = '/api/stock/count/';
        break;
    case 'take':
        formTitle = '移除库存';
        actionTitle = '拿出';
        url = '/api/stock/remove/';
        break;
    case 'add':
        formTitle = '添加库存';
        actionTitle = '添加';
        url = '/api/stock/add/';
        break;
    case 'delete':
        formTitle = '删除库存';
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
        <th>零件</th>
        <th>庫存</th>
        <th>地點</th>
        <th>${actionTitle || ''}</th>
        <th></th>
    </tr>
    </thead>
    <tbody>
    `;

    var itemCount = 0;

    for (var idx = 0; idx < items.length; idx++) {

        const item = items[idx];

        if ((item.serial != null) && (item.serial != '') && !allowSerializedStock) {
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

        var status = stockStatusDisplay(item.status_custom_key, {
            classes: 'float-right'
        });

        let quantityString = '';

        var location = locationDetail(item, false);

        if (item.location_detail) {
            location = item.location_detail.pathstring;
        }

        if (!item.serial) {
            quantityString = `${item.quantity}`;

            if (item.part_detail?.units) {
                quantityString += `<small> [${item.part_detail.units}]</small>`;
            }
        } else {
            quantityString = `#${item.serial}`;
        }

        if (item.batch) {
            quantityString += ` - <small>队列: ${item.batch}</small>`;
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
                    title: readonly ? '序列化库存的数量不能调整' : '指定库存数量',
                    required: true,
                },
                {
                    hideLabels: true,
                }
            );
        }

        let buttons = '';

        if (allowExtraFields) {
            buttons += makeIconButton(
                'fa-layer-group',
                'button-row-add-batch',
                pk,
                '调整批次代码',
                {
                    collapseTarget: `row-batch-${pk}`
                }
            );

            buttons += makeIconButton(
                'fa-boxes',
                'button-row-add-packaging',
                pk,
                '调整包装',
                {
                    collapseTarget: `row-packaging-${pk}`
                }
            );
        }

        buttons += makeRemoveButton(
            'button-stock-item-remove',
            pk,
            '移除库存项',
        );

        buttons = wrapButtons(buttons);

        // Add in options for "batch code" and "serial numbers"
        const batch_input = constructField(
            `items_batch_code_${pk}`,
            {
                type: 'string',
                required: false,
                label: '批号',
                help_text: '输入入库项目的批号',
                icon: 'fa-layer-group',
                value: item.batch,
            },
            {
                hideLabels: true,
            }
        );

        const packaging_input = constructField(
            `items_packaging_${pk}`,
            {
                type: 'string',
                required: false,
                label: '打包',
                help_text: '指定进货库存项的包装',
                icon: 'fa-boxes',
                value: item.packaging,
            },
            {
                hideLabels: true,
            }
        );

        html += `
        <tr id='stock_item_${pk}' class='stock-item-row'>
            <td id='part_${pk}'>${thumb} ${item.part_detail.full_name}</td>
            <td id='stock_${pk}'>${quantityString}${status}</td>
            <td id='location_${pk}'>${location}</td>
            <td id='action_${pk}'>
                <div id='div_id_${pk}'>
                    ${actionInput}
                    <div id='errors-${pk}'></div>
                </div>
            </td>
            <td id='buttons_${pk}'>${buttons}</td>
        </tr>
        <!-- Hidden row for extra data entry -->
        <tr id='row-batch-${pk}' class='collapse'>
            <td colspan='2'></td>
            <th>队列</th>
            <td colspan='2'>${batch_input}</td>
            <td></td>
        </tr>
        <tr id='row-packaging-${pk}' class='collapse'>
            <td colspan='2'></td>
            <th>打包</th>
            <td colspan='2'>${packaging_input}</td>
            <td></td>
        </tr>`;

        itemCount += 1;
    }

    if (itemCount == 0) {
        showAlertDialog(
            '选择库存项',
            '至少选择一个可用库存项目',
        );

        return;
    }

    html += `</tbody></table>`;

    var extraFields = {};

    if (specifyLocation) {

        // If a common location is specified, use that as the default
        let commonLocation = null;

        for (const item of items) {

            if (item.location == commonLocation) {
                continue;
            }

            if (commonLocation == null) {
                commonLocation = item.location;
            } else {
                commonLocation = null;
                break;
            }
        }

        extraFields.location = {
            value: commonLocation,
            filters: {
                structural: false,
            },
        };
    }

    if (action != 'delete') {
        extraFields.notes = {};
    }

    constructForm(url, {
        method: 'POST',
        fields: extraFields,
        preFormContent: html,
        confirm: true,
        confirmMessage: '确认库存调整',
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
                let pk = item.pk;

                // Does the row exist in the form?
                let row = $(opts.modal).find(`#stock_item_${pk}`);

                if (row.exists()) {

                    item_pk_values.push(pk);

                    let quantity = getFormFieldValue(`items_quantity_${pk}`, {}, opts);
                    let line = {
                        pk: pk,
                        quantity: quantity
                    };

                    if (getFormFieldElement(`items_batch_code_${pk}`).exists()) {
                        line.batch = getFormFieldValue(`items_batch_code_${pk}`);
                    }

                    if (getFormFieldElement(`items_packaging_${pk}`).exists()) {
                        line.packaging = getFormFieldValue(`items_packaging_${pk}`);
                    }

                    data.items.push(line);
                }
            });

            // Delete action is handled differently
            if (action == 'delete') {

                var ids = [];

                items.forEach(function(item) {
                    ids.push(item.pk);
                });

                showModalSpinner(opts.modal, true);
                inventreeDelete(
                    '/api/stock/',
                    {
                        data: {
                            items: ids,
                        },
                        success: function(response) {
                            $(opts.modal).modal('hide');
                            options.success(response);
                        }
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
        return `<span class='badge badge-right rounded-pill bg-success'>合格</span>`;
    } else {
        return `<span class='badge badge-right rounded-pill bg-danger'>不合格</span>`;
    }
}

function noResultBadge() {
    return `<span class='badge badge-right rounded-pill bg-info'>无结果</span>`;
}

function formatDate(row, date, options={}) {
    // Function for formatting date field
    var html = renderDate(date, options);

    if (row.user_detail && !options.no_user_detail) {
        html += `<span class='badge badge-right rounded-pill bg-secondary'>${row.user_detail.username}</span>`;
    }

    return html;
}

/* Construct set of default fields for a StockItemTestResult */
function stockItemTestResultFields(options={}) {
    let fields = {
        template: {
            filters: {
                include_inherited: true,
            }
        },
        result: {},
        value: {},
        attachment: {},
        notes: {
            icon: 'fa-sticky-note',
        },
        test_station: {},
        started_datetime: {
            icon: 'fa-calendar-alt',
        },
        finished_datetime: {
            icon: 'fa-calendar-alt',
        },
        stock_item: {
            hidden: true,
        },
    };

    if (options.part) {
        fields.template.filters.part = options.part;
    }

    if (options.stock_item) {
        fields.stock_item.value = options.stock_item;
    }

    return fields;
}

/*
 * Load StockItemTestResult table
 */
function loadStockTestResultsTable(table, options) {

    // Setup filters for the table
    var filterTarget = options.filterTarget || '#filter-list-stocktests';

    var filterKey = options.filterKey || options.name || 'stocktests';

    let params = {
        part: options.part,
        include_inherited: true,
        enabled: true,
    };

    var filters = loadTableFilters(filterKey, params);

    setupFilterList(filterKey, table, filterTarget);

    function makeButtons(row, grouped) {

        // Helper function for rendering buttons

        let html = '';


        if (row.requires_attachment == false && row.requires_value == false && !row.result) {
            // Enable a "quick tick" option for this test result
            html += makeIconButton('fa-check-circle icon-green', 'button-test-tick', row.test_name, '通过测试');
        }

        html += makeIconButton('fa-plus icon-green', 'button-test-add', row.templateId, '新增测试结果');

        if (!grouped && row.result != null) {
            html += makeEditButton('button-test-edit', row.testId, '编辑测试结果');
            html += makeDeleteButton('button-test-delete', row.testId, '删除测试结果');
        }

        return wrapButtons(html);
    }

    var parent_node = 'parent node';

    table.inventreeTable({
        url: '/api/part/test-template/',
        method: 'get',
        name: 'testresult',
        treeEnable: true,
        rootParentId: parent_node,
        parentIdField: 'parent',
        idField: 'pk',
        uniqueId: 'pk',
        treeShowField: 'test_name',
        formatNoMatches: function() {
            return '未找到测试结果';
        },
        queryParams: filters,
        original: params,
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
                title: '测试',
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
                field: 'description',
                title: '描述',
                formatter: function(value, row) {
                    return row.description || row.test_description;
                }
            },
            {
                field: 'value',
                title: '值',
                formatter: function(value, row) {
                    var html = value;

                    if (row.attachment) {
                        let text = makeIconBadge('fa-file-alt', '');
                        html += renderLink(text, row.attachment, {download: true});
                    }

                    return html;
                }
            },
            {
                field: 'notes',
                title: '备注',
            },
            {
                field: 'date',
                title: '测试日期',
                sortable: true,
                formatter: function(value, row) {
                    return formatDate(row, row.date);
                },
            },
            {
                field: 'test_station',
                title: '测试站',
                visible: false,
            },
            {
                field: 'started_timestamp',
                title: '测试已开始',
                sortable: true,
                visible: false,
                formatter: function(value, row) {
                    return formatDate(row, row.started_datetime, {showTime: true, no_user_detail: true});
                },
            },
            {
                field: 'finished_timestamp',
                title: '测试已完成',
                sortable: true,
                visible: false,
                formatter: function(value, row) {
                    return formatDate(row, row.finished_datetime, {showTime: true, no_user_detail: true});
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

            // Construct an initial dataset based on the returned templates
            let results = tableData.map((template) => {
                return {
                    ...template,
                    templateId: template.pk,
                    parent: parent_node,
                    results: []
                };
            });

            // Once the test template data are loaded, query for test results

            var filters = loadTableFilters(filterKey);

            var query_params = {
                stock_item: options.stock_item,
                user_detail: true,
                enabled: true,
                attachment_detail: true,
                template_detail: false,
                ordering: '-date',
            };

            if ('result' in filters) {
                query_params.result = filters.result;
            }

            if ('include_installed' in filters) {
                query_params.include_installed = filters.include_installed;
            }

            inventreeGet(
                '/api/stock/test/',
                query_params,
                {
                    success: function(data) {

                        data.sort((a, b) => {
                            return a.pk < b.pk;
                        }).forEach((row) => {
                            let idx = results.findIndex((template) => {
                                return template.templateId == row.template;
                            });

                            if (idx > -1) {

                                results[idx].results.push(row);

                                // Check if a test result is already recorded
                                if (results[idx].testId) {
                                    // Push this result into the results array
                                    results.push({
                                        ...results[idx],
                                        ...row,
                                        parent: results[idx].templateId,
                                        testId: row.pk,
                                    });
                                } else {
                                    // First result - update the parent row
                                    results[idx] = {
                                        ...row,
                                        ...results[idx],
                                        testId: row.pk,
                                    };
                                }
                            }
                        });

                        // Push data back into the table
                        table.bootstrapTable('load', results);
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
            '/api/stock/test/',
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

        var templateId = button.attr('pk');

        let fields = stockItemTestResultFields();

        fields['stock_item']['value'] = options.stock_item;
        fields['template']['value'] = templateId;
        fields['template']['filters']['part'] = options.part;

        if (!options.test_station_fields) {
            delete fields['test_station'];
            delete fields['started_datetime'];
            delete fields['finished_datetime'];
        }

        constructForm('/api/stock/test/', {
            method: 'POST',
            fields: fields,
            title: '添加测试结果',
            onSuccess: reloadTestTable,
        });
    });

    // Edit a test result
    $(table).on('click', '.button-test-edit', function() {
        var button = $(this);

        var pk = button.attr('pk');

        var url = `/api/stock/test/${pk}/`;

        constructForm(url, {
            fields: stockItemTestResultFields(),
            title: '编辑测试结果',
            onSuccess: reloadTestTable,
        });
    });

    // Delete a test result
    $(table).on('click', '.button-test-delete', function() {
        var button = $(this);

        var pk = button.attr('pk');

        var url = `/api/stock/test/${pk}/`;

        var html = `
        <div class='alert alert-block alert-danger'>
        <strong>删除测试结果</strong>
        </div>`;

        constructForm(url, {
            method: 'DELETE',
            title: '删除测试结果',
            onSuccess: reloadTestTable,
            preFormContent: html,
        });
    });
}


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
function locationDetail(row, showLink=true) {

    // Display text
    let text = '';

    // URL (optional)
    let url = '';

    if (row.consumed_by) {
        text = '被工單消耗的';
        url = `/build/${row.consumed_by}/`;
    } else if (row.is_building && row.build) {
        // StockItem is currently being built!
        text = '生产中';
        url = `/build/${row.build}/`;
    } else if (row.belongs_to) {
        // StockItem is installed inside a different StockItem
        text = `已安装库存项目 ${row.belongs_to}`;
        url = `/stock/item/${row.belongs_to}/?display=installed-items`;
    } else if (row.customer) {
        // StockItem has been assigned to a customer
        text = '已配送到客户';
        url = `/company/${row.customer}/?display=assigned-stock`;
    } else if (row.sales_order) {
        // StockItem has been assigned to a sales order
        text = '分配给销售订单';
        url = `/order/sales-order/${row.sales_order}/`;
    } else if (row.location && row.location_detail) {
        text = shortenString(row.location_detail.pathstring);
        url = `/stock/location/${row.location}/`;
    } else {
        text = '<i>未设置库存位置</i>';
        url = '';
    }

    if (showLink && url) {
        return renderLink(text, url);
    } else {
        return text;
    }
}


/*
 * Construct a set of custom actions for the stock table
 */
function makeStockActions(table) {
    let actions = [
        {
            label: 'add',
            icon: 'fa-plus-circle icon-green',
            title: '增加库存',
            permission: 'stock.change',
            callback: function(data) {
                stockAdjustment('add', data, table);
            }
        },
        {
            label: 'remove',
            icon: 'fa-minus-circle icon-red',
            title: '移除库存',
            permission: 'stock.change',
            callback: function(data) {
                stockAdjustment('take', data, table);
            },
        },
        {
            label: 'stocktake',
            icon: 'fa-check-circle icon-blue',
            title: '清点库存',
            permission: 'stock.change',
            callback: function(data) {
                stockAdjustment('count', data, table);
            },
        },
        {
            label: 'move',
            icon: 'fa-exchange-alt icon-blue',
            title: '转移库存',
            permission: 'stock.change',
            callback: function(data) {
                stockAdjustment('move', data, table);
            }
        },
        {

            label: 'status_custom_key',
            icon: 'fa-info-circle icon-blue',
            title: '更改库存状态',
            permission: 'stock.change',
            callback: function(data) {
                setStockStatus(data, {table: table});
            },
        },
        {
            label: 'merge',
            icon: 'fa-object-group',
            title: '合并库存',
            permission: 'stock.change',
            callback: function(data) {
                mergeStockItems(data, {
                    success: function(response) {
                        $(table).bootstrapTable('refresh');

                        showMessage('合并的库存项', {
                            style: 'success',
                        });
                    }
                });
            },
        },
        {
            label: 'order',
            icon: 'fa-shopping-cart',
            title: '订单库存',
            permission: 'stock.change',
            callback: function(data) {
                let parts = [];

                data.forEach(function(item) {
                    var part = item.part_detail;

                    if (part) {
                        parts.push(part);
                    }
                });

                orderParts(parts, {});
            },
        },
        {
            label: 'assign',
            icon: 'fa-user-tie',
            title: '分配给客户',
            permission: 'stock.change',
            callback: function(data) {
                assignStockToCustomer(data, {
                    success: function() {
                        $(table).bootstrapTable('refresh');
                    }
                });
            },
        },
        {
            label: 'delete',
            icon: 'fa-trash-alt icon-red',
            title: '删除库存',
            permission: 'stock.delete',
            callback: function(data) {
                stockAdjustment('delete', data, table);
            },
        }
    ];

    return actions;

}


/* Load data into a stock table with adjustable options.
 * Fetches data (via AJAX) and loads into a bootstrap table.
 * Also links in default button callbacks.
 *
 * Options:
 *  url - URL for the stock query
 *  params - query params for augmenting stock data request
 *  buttons - Which buttons to link to stock selection callbacks
 *  filterList - <ul> element where filters are displayed
 *  disableFilters: If true, disable custom filters
 */
function loadStockTable(table, options) {

    options.params = options.params || {};

    // List of user-params which override the default filters
    options.params['location_detail'] = true;
    options.params['part_detail'] = true;

    // Determine if installed items are displayed in the table
    let show_installed_items = global_settings.STOCK_SHOW_INSTALLED_ITEMS;

    let filters = {};

    if (!options.disableFilters) {

        const filterTarget = options.filterTarget || '#filter-list-stock';
        const filterKey = options.filterKey || options.name || 'stock';

        filters = loadTableFilters(filterKey, options.params);

        setupFilterList(filterKey, table, filterTarget, {
            download: true,
            report: {
                key: 'stockitem',
            },
            labels: {
                model_type: 'stockitem',
            },
            singular_name: '库存项',
            plural_name: '库存项',
            barcode_actions: [
                {
                    icon: 'fa-sitemap',
                    label: 'scantolocation',
                    title: '扫描到位置',
                    permission: 'stock.change',
                    callback: function(items) {
                        scanItemsIntoLocation(items);
                    }
                }
            ],
            custom_actions: [
                {
                    actions: makeStockActions(table),
                    icon: 'fa-boxes',
                    title: '库存操作',
                    label: 'stock',
                }
            ]
        });
    }

    filters = Object.assign(filters, options.params);

    var col = null;

    var columns = [
        {
            checkbox: true,
            title: '选择',
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
        field: 'part',
        title: '零件',
        sortName: 'part__name',
        visible: options.params['part_detail'],
        switchable: options.params['part_detail'],
        formatter: function(value, row) {

            let html = '';

            if (show_installed_items && row.installed_items > 0) {
                if (row.installed_items_received) {
                    // Data received, ignore
                } else if (row.installed_items_requested) {
                    html += `<span class='fas fa-sync fa-spin'></span>`;
                } else {
                    html += `
                    <a href='#' pk='${row.pk}' class='load-sub-items' id='load-sub-items-${row.pk}'>
                        <span class='fas fa-sync-alt' title='加载已安装的项目'></span>
                    </a>`;
                }
            }

            html += partDetail(row.part_detail, {
                thumb: true,
                link: true,
                icons: true,
            });

            return html;
        }
    };

    if (!options.params.ordering) {
        col['sortable'] = true;
    }

    columns.push(col);

    col = {
        field: 'IPN',
        title: '内部零件号 IPN',
        sortName: 'part__IPN',
        visible: options.params['part_detail'],
        switchable: options.params['part_detail'],
        formatter: function(value, row) {
            var ipn = row.part_detail.IPN;
            if (ipn) {
                return renderClipboard(withTitle(shortenString(ipn), ipn));
            } else {
                return '-';
            }
        },
    };

    if (!options.params.ordering) {
        col['sortable'] = true;
    }

    columns.push(col);

    columns.push({
        field: 'part_detail.description',
        title: '描述',
        visible: options.params['part_detail'],
        switchable: options.params['part_detail'],
        formatter: function(value, row) {
            var description = row.part_detail.description;
            return withTitle(shortenString(description), description);
        }
    });

    col = {
        field: 'quantity',
        sortName: 'stock',
        title: '庫存',
        sortable: true,
        formatter: function(value, row) {

            var val = '';

            if (row.serial && row.quantity == 1) {
                // If there is a single unit with a serial number, use the serial number
                val = '# ' + row.serial;
            } else {
                // Format floating point numbers with this one weird trick
                val = formatDecimal(value);

                if (row.part_detail && row.part_detail.units) {
                    val += ` ${row.part_detail.units}`;
                }
            }

            var html = renderLink(val, `/stock/item/${row.pk}/`);

            if (row.is_building) {
                html += makeIconBadge('fa-tools', '库存项正在生产');
            }

            if (row.sales_order) {
                // Stock item has been assigned to a sales order
                html += makeIconBadge('fa-truck', '分配给销售订单的库存项目');
            } else if (row.customer) {
                // StockItem has been assigned to a customer
                html += makeIconBadge('fa-user', '分配给客户的库存项');
            } else if (row.allocated) {
                if (row.serial != null && row.quantity == 1) {
                    html += makeIconBadge('fa-bookmark icon-yellow', '已分配序列化库存项');
                } else if (row.allocated >= row.quantity) {
                    html += makeIconBadge('fa-bookmark icon-yellow', '库存项目已完全分配');
                } else {
                    html += makeIconBadge('fa-bookmark', '库存项目已部分分配');
                }
            } else if (row.belongs_to) {
                html += makeIconBadge('fa-box', '库存项目已安装在另一个项目中');
            } else if (row.consumed_by) {
                html += makeIconBadge('fa-tools', '库存项已被生产订单消耗');
            }

            if (row.expired) {
                html += makeIconBadge('fa-calendar-times icon-red', '库存项已过期');
            } else if (row.stale) {
                html += makeIconBadge('fa-stopwatch', '库存项即将过期');
            }

            // Special stock status codes
            if (row.status == stockCodes.REJECTED.key) {
                html += makeIconBadge('fa-times-circle icon-red', '库存项已被拒绝');
            } else if (row.status == stockCodes.LOST.key) {
                html += makeIconBadge('fa-question-circle', '库存项丢失了');
            } else if (row.status == stockCodes.DESTROYED.key) {
                html += makeIconBadge('fa-skull-crossbones', '库存项已销毁');
            }

            if (row.quantity <= 0) {
                html += `<span class='badge badge-right rounded-pill bg-danger'>已用完</span>`;
            }

            return html;
        },
        footerFormatter: function(data) {
            // Display "total" stock quantity of all rendered rows
            let total = 0;

            // Keep track of the whether all units are the same
            // If different units are found, we cannot aggregate the quantities
            let units = new Set();

            data.forEach(function(row) {

                units.add(row.part_detail.units || null);

                if (row.quantity != null) {
                    total += row.quantity;
                }
            });

            if (data.length == 0) {
                return '-';
            } else if (units.size > 1) {
                return '-';
            } else {
                let output = `${total}`;

                if (units.size == 1) {
                    let unit = units.values().next().value;

                    if (unit) {
                        output += ` [${unit}]`;
                    }
                }

                return output;
            }
        }
    };

    columns.push(col);

    col = {
        field: 'status_custom_key',
        title: '狀態',
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
        title: '队列',
    };

    if (!options.params.ordering) {
        col['sortable'] = true;
    }

    columns.push(col);

    col = {
        field: 'location_detail.pathstring',
        title: '地點',
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
        title: '库存盘点',
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
        title: '有效期至',
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
        title: '最近更新',
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
        title: '采购订单',
        formatter: function(value, row) {
            if (!value) {
                return '-';
            }

            var link = `/order/purchase-order/${row.purchase_order}/`;
            var text = `${row.purchase_order}`;

            if (row.purchase_order_reference) {
                text = row.purchase_order_reference;
            }

            return renderLink(text, link);
        }
    });

    col = {

        field: 'supplier_part',
        title: '供应商零件',
        visible: options.params['supplier_part_detail'] || false,
        switchable: options.params['supplier_part_detail'] || false,
        formatter: function(value, row) {
            if (!value) {
                return '-';
            }

            var link = `/supplier-part/${row.supplier_part}/?display=part-stock`;

            var text = '';

            if (row.supplier_part_detail) {
                text = `${row.supplier_part_detail.SKU}`;
            } else {
                text = `<i>未指定供应商零件</i>`;
            }

            return renderClipboard(renderLink(text, link));
        }
    };

    if (!options.params.ordering) {
        col.sortable = true;
        col.sortName = 'SKU';
    }

    columns.push(col);

    columns.push({
        field: 'purchase_price',
        title: '采购价格',
        sortable: false,
        formatter: function(value, row) {
            let html = formatCurrency(value, {
                currency: row.purchase_price_currency,
            });

            var base = baseCurrency();

            if (row.purchase_price_currency != base) {
                let converted = convertCurrency(
                    row.purchase_price,
                    row.purchase_price_currency,
                    base,
                    getCurrencyConversionRates(),
                );

                if (converted) {
                    converted = formatCurrency(converted, {currency: baseCurrency()});
                    html += `<br><small><em>${converted}</em></small>`;
                }
            }

            return html;
        }
    });

    // Total value of stock
    // This is not sortable, and may default to the 'price range' for the parent part
    columns.push({
        field: 'stock_value',
        title: '库存值',
        sortable: false,
        switchable: true,
        formatter: function(value, row) {
            let min_price = row.purchase_price;
            let max_price = row.purchase_price;
            let currency = row.purchase_price_currency;

            if (min_price == null && max_price == null && row.part_detail) {
                min_price = row.part_detail.pricing_min;
                max_price = row.part_detail.pricing_max;
                currency = baseCurrency();
            }

            if (row.quantity <= 0) {
                return '-';
            }

            return formatPriceRange(
                min_price,
                max_price,
                {
                    quantity: row.quantity,
                    currency: currency
                }
            );
        },
        footerFormatter: function(data) {
            // Display overall range of value for the selected items
            let rates = getCurrencyConversionRates();
            let base = baseCurrency();

            let min_price = calculateTotalPrice(
                data,
                function(row) {
                    return row.quantity * (row.purchase_price || row.part_detail.pricing_min);
                },
                function(row) {
                    if (row.purchase_price) {
                        return row.purchase_price_currency;
                    } else {
                        return base;
                    }
                },
                {
                    currency: base,
                    rates: rates,
                    raw: true,
                }
            );

            let max_price = calculateTotalPrice(
                data,
                function(row) {
                    return row.quantity * (row.purchase_price || row.part_detail.pricing_max);
                },
                function(row) {
                    if (row.purchase_price) {
                        return row.purchase_price_currency;
                    } else {
                        return base;
                    }
                },
                {
                    currency: base,
                    rates: rates,
                    raw: true,
                }
            );

            return formatPriceRange(
                min_price,
                max_price,
                {
                    currency: base,
                }
            );
        }
    });

    columns.push({
        field: 'packaging',
        title: '打包',
    },
    {
        field: 'notes',
        title: '备注',
    });

    // Function to request subset of items which are installed *within* a particular item
    function requestInstalledItems(stock_item) {
        inventreeGet(
            '/api/stock/',
            {
                belongs_to: stock_item,
                part_detail: true,
                supplier_detail: true,
            },
            {
                success: function(response) {
                    // Add the returned stock items into the table
                    let row  = table.bootstrapTable('getRowByUniqueId', stock_item);
                    row.installed_items_received = true;

                    for (let ii = 0; ii < response.length; ii++) {
                        response[ii].belongs_to_item = stock_item;
                    }

                    table.bootstrapTable('updateByUniqueId', stock_item, row, true);
                    table.bootstrapTable('append', response);

                    // Auto-expand the newly added data
                    $(`.treegrid-${stock_item}`).treegrid('expand');
                },
                error: function(xhr) {
                    console.error(`Error requesting installed items for ${stock_item}`);
                    showApiError(xhr);
                }
            }
        );
    }

    let parent_id = 'top-level';
    let loaded = false;

    table.inventreeTable({
        method: 'get',
        formatNoMatches: function() {
            return '没有符合查询的库存项目';
        },
        url: options.url || '/api/stock/',
        queryParams: filters,
        sidePagination: 'server',
        name: 'stock',
        original: options.params,
        showColumns: true,
        showFooter: true,
        columns: columns,
        treeEnable: show_installed_items,
        rootParentId: show_installed_items ? parent_id : null,
        parentIdField: show_installed_items ? 'belongs_to_item' : null,
        uniqueId: 'pk',
        idField: 'pk',
        treeShowField: show_installed_items ? 'part' : null,
        onLoadSuccess: function(data) {
            let records = data.results || data;

            // Set the 'parent' ID for each root item
            if (!loaded && show_installed_items) {
                for (let i = 0; i < records.length; i++) {
                    records[i].belongs_to_item = parent_id;
                }

                loaded = true;
                $(table).bootstrapTable('load', records);
            }
        },
        onPostBody: function() {
            if (show_installed_items) {
                table.treegrid({
                    treeColumn: 1,
                });

                table.treegrid('collapseAll');

                // Callback for 'load sub-items' button
                table.find('.load-sub-items').click(function(event) {
                    event.preventDefault();

                    let pk = $(this).attr('pk');
                    let row = table.bootstrapTable('getRowByUniqueId', pk);

                    requestInstalledItems(row.pk);

                    row.installed_items_requested = true;
                    table.bootstrapTable('updateByUniqueId', pk, row, true);
                });
            }
        }
    });

    var buttons = [
        '#stock-options',
    ];

    if (global_settings.BARCODE_ENABLE) {
        buttons.push('#stock-barcode-options');
    }

    // Callback for 'change status' button
    $('#multi-item-status').click(function() {
        let selections = getTableData(table);
        let items = [];

        selections.forEach(function(item) {
            items.push(item.pk);
        });




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
        params.depth = global_settings.INVENTREE_TREE_DEPTH;
    }

    var filterKey = options.filterKey || options.name || 'location';

    let filters = loadTableFilters(filterKey, params);

    setupFilterList(filterKey, table, filterListElement, {
        download: true,
        labels: {
            model_type: 'stocklocation',
        },
        singular_name: '库存位置',
        plural_name: '库存地点',
    });

    filters = Object.assign(filters, params);

    // Function to request sub-location items
    function requestSubItems(parent_pk) {
        inventreeGet(
            options.url || '/api/stock/location/',
            {
                parent: parent_pk,
            },
            {
                success: function(response) {
                    // Add the returned sub-items to the table
                    for (var idx = 0; idx < response.length; idx++) {
                        response[idx].parent = parent_pk;
                    }

                    const row = $(table).bootstrapTable('getRowByUniqueId', parent_pk);
                    row.subReceived = true;

                    $(table).bootstrapTable('updateByUniqueId', parent_pk, row, true);

                    table.bootstrapTable('append', response);
                },
                error: function(xhr) {
                    console.error('Error requesting sub-locations for location=' + parent_pk);
                    showApiError(xhr);
                }
            }
        );
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
        url: options.url || '/api/stock/location/',
        queryParams: filters,
        name: 'location',
        original: params,
        sortable: true,
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

                    // Callback for 'load sub location' button
                    $(table).find('.load-sub-location').click(function(event) {
                        event.preventDefault();

                        const pk = $(this).attr('pk');
                        const row = $(table).bootstrapTable('getRowByUniqueId', pk);

                        // Request sub-location for this location
                        requestSubItems(row.pk);

                        row.subRequested = true;
                        $(table).bootstrapTable('updateByUniqueId', pk, row, true);
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
                    title: '按列表显示',
                    id: 'view-location-list',
                },
                event: () => {
                    inventreeSave('location-tree-view', 0);

                    // Adjust table options
                    options.treeEnable = false;
                    options.serverSort = true;
                    options.search = true;
                    options.pagination = true;

                    // Destroy and re-create the table
                    table.bootstrapTable('destroy');
                    loadStockLocationTable(table, options);
                }
            },
            {
                icon: 'fas fa-sitemap',
                attributes: {
                    title: '树状显示',
                    id: 'view-location-tree',
                },
                event: () => {
                    inventreeSave('location-tree-view', 1);

                    // Adjust table options
                    options.treeEnable = true;
                    options.serverSort = false;
                    options.search = false;
                    options.pagination = false;

                    // Destroy and re-create the table
                    table.bootstrapTable('destroy');
                    loadStockLocationTable(table, options);
                }
            }
        ] : [],
        columns: [
            {
                checkbox: true,
                title: '选择',
                searchable: false,
                switchable: false,
            },
            {
                field: 'name',
                title: '名稱',
                switchable: true,
                sortable: true,
                formatter: function(value, row) {
                    let html = '';

                    if (row._level >= global_settings.INVENTREE_TREE_DEPTH && !row.subReceived) {
                        if (row.subRequested) {
                            html += `<a href='#'><span class='fas fa-sync fa-spin'></span></a>`;
                        } else {
                            html += `
                                <a href='#' pk='${row.pk}' class='load-sub-location'>
                                    <span class='fas fa-sync-alt' title='加载次级地点'></span>
                                </a> `;
                        }
                    }

                    if (row.icon) {
                        html += `<span class="${getApiIconClass(row.icon)} me-1"></span>`;
                    }

                    html += renderLink(
                        value,
                        `/stock/location/${row.pk}/`
                    );

                    return html;
                },
            },
            {
                field: 'description',
                title: '描述',
                switchable: true,
                sortable: false,
                formatter: function(value) {
                    return withTitle(shortenString(value), value);
                }
            },
            {
                field: 'pathstring',
                title: '路徑',
                switchable: true,
                sortable: true,
                formatter: function(value) {
                    return withTitle(shortenString(value), value);
                }
            },
            {
                field: 'items',
                title: '库存项',
                switchable: true,
                sortable: true,
            },
            {
                field: 'structural',
                title: '结构性',
                switchable: true,
                sortable: false,
                formatter: function(value) {
                    return yesNoLabel(value);
                }
            },
            {
                field: 'external',
                title: '外部',
                switchable: true,
                sortable: false,
                formatter: function(value) {
                    return yesNoLabel(value);
                }
            },
            {
                field: 'location_type',
                title: '位置类型',
                switchable: true,
                sortable: false,
                formatter: function(value, row) {
                    if (row.location_type_detail) {
                        return row.location_type_detail.name;
                    }
                }
            },
        ]
    });
}

/*
 * Load stock history / tracking table for a given StockItem
 */
function loadStockTrackingTable(table, options) {

    var cols = [];

    const filterKey = 'stocktracking';

    let params = options.params || {};

    let filters = loadTableFilters(filterKey, params);

    setupFilterList(filterKey, table, '#filter-list-stocktracking');

    // Date
    cols.push({
        field: 'date',
        title: '日期',
        sortable: true,
        formatter: function(value) {
            return renderDate(value, {showTime: true});
        }
    });

    // Stock transaction description
    cols.push({
        field: 'label',
        title: '描述',
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
        title: '详情',
        formatter: function(details, row) {

            if (!details || !Object.keys(details).length) {
                return `<small><em>无更改</em></small>`;
            }

            let html = `<table class='table table-condensed' id='tracking-table-${row.pk}'>`;

            // Part information
            if (details.part) {
                html += `<tr><th>零件</th><td>`;

                if (details.part_detail) {
                    html += renderLink(details.part_detail.full_name, `/part/${details.part}/`);
                } else {
                    html += `零件信息不可用`;
                }

                html += `</td></tr>`;
            }

            // Location information
            if (details.location) {

                html += `<tr><th>地點</th>`;

                html += '<td>';

                if (details.location_detail) {
                    // A valid location is provided

                    html += renderLink(
                        details.location_detail.pathstring,
                        details.location_detail.url,
                    );
                } else {
                    // An invalid location (may have been deleted?)
                    html += `<i>位置不再存在</i>`;
                }

                html += '</td></tr>';
            }

            // BuildOrder Information
            if (details.buildorder) {
                html += `<tr><th>生產工單</th>`;
                html += `<td>`;

                if (details.buildorder_detail) {
                    html += renderLink(
                        details.buildorder_detail.reference,
                        `/build/${details.buildorder}/`
                    );
                } else {
                    html += `<i>生产订单不再存在</i>`;
                }
            }

            // PurchaseOrder Information
            if (details.purchaseorder) {
                html += `<tr><th>采购订单</th>`;
                html += '<td>';

                if (details.purchaseorder_detail) {
                    html += renderLink(
                        details.purchaseorder_detail.reference,
                        `/order/purchase-order/${details.purchaseorder}/`
                    );
                } else {
                    html += `<i>采购订单不再存在</i>`;
                }

                html += '</td></tr>';
            }

            // SalesOrder information
            if (details.salesorder) {
                html += `<tr><th>销售订单</th>`;
                html += '<td>';

                if (details.salesorder_detail) {
                    html += renderLink(
                        details.salesorder_detail.reference,
                        `/order/sales-order/${details.salesorder}/`
                    );
                } else {
                    html += `<em>销售订单不再存在</em>`;
                }

                html += `</td></tr>`;
            }

            // ReturnOrder information
            if (details.returnorder) {
                html += `<tr><th>退货订单</th>`;
                html += '<td>';

                if (details.returnorder_detail) {
                    html += renderLink(
                        details.returnorder_detail.reference,
                        `/order/return-order/${details.returnorder}/`
                    );
                } else {
                    html += `<em>退货订单已不存在</em>`;
                }

                html += `</td></tr>`;
            }

            // Customer information
            if (details.customer) {

                html += `<tr><th>客户</td>`;

                html += '<td>';

                if (details.customer_detail) {
                    html += renderLink(
                        details.customer_detail.name,
                        details.customer_detail.url
                    );
                } else {
                    html += `<i>客户已不存在</i>`;
                }

                html += '</td></tr>';
            }

            // Stockitem information
            if (details.stockitem) {
                html += '<tr><th>庫存品項</td>';

                html += '<td>';

                if (details.stockitem_detail) {
                    html += renderLink(
                        details.stockitem,
                        `/stock/item/${details.stockitem}/`
                    );
                } else {
                    html += `<i>库存项已不存在</i>`;
                }

                html += '</td></tr>';
            }

            // Status information
            if (details.status_custom_key) {
                html += `<tr><th>狀態</td>`;

                html += '<td>';
                html += stockStatusDisplay(details.status_custom_key);
                html += '</td></tr>';

            }

            // Quantity information
            if (details.added) {
                html += '<tr><th>已添加</th>';

                html += `<td>${details.added}</td>`;

                html += '</tr>';
            }

            if (details.removed) {
                html += '<tr><th>已删除</th>';

                html += `<td>${details.removed}</td>`;

                html += '</tr>';
            }

            if (details.quantity) {
                html += '<tr><th>數量</th>';

                html += `<td>${details.quantity}</td>`;

                html += '</tr>';
            }

            html += '</table>';

            return html;
        }
    });

    cols.push({
        field: 'user',
        title: '使用者',
        formatter: function(value, row) {
            if (value) {
                // TODO - Format the user's first and last names
                return row.user_detail.username;
            } else {
                return `<i>没有用户信息</i>`;
            }
        }
    });

    table.inventreeTable({
        method: 'get',
        queryParams: filters,
        original: params,
        columns: cols,
        url: options.url,
    });

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
        url: '/api/stock/',
        queryParams: {
            belongs_to: options.stock_item,
            part_detail: true,
        },
        formatNoMatches: function() {
            return '没有已安装的项目';
        },
        columns: [
            {
                field: 'part',
                title: '零件',
                formatter: function(value, row) {
                    var html = '';

                    if (row.part_detail) {
                        html += imageHoverIcon(row.part_detail.thumbnail);
                        html += renderLink(row.part_detail.full_name, `/stock/item/${row.pk}/`);
                    }

                    return html;
                }
            },
            {
                field: 'quantity',
                title: '數量',
                formatter: function(value, row) {

                    var html = '';

                    if (row.serial && row.quantity == 1) {
                        html += `系列: ${row.serial}`;
                    } else {
                        html += `${row.quantity}`;
                    }

                    return renderLink(html, `/stock/item/${row.pk}/`);
                }
            },
            {
                field: 'status_custom_key',
                title: '狀態',
                formatter: function(value) {
                    return stockStatusDisplay(value);
                }
            },
            {
                field: 'batch',
                title: '队列',
            },
            {
                field: 'buttons',
                title: '',
                switchable: false,
                visible: options.can_edit,
                formatter: function(value, row) {
                    let pk = row.pk;
                    let html = '';

                    if (options.can_edit) {
                        html += makeIconButton('fa-unlink', 'button-uninstall', pk, '卸载库存项');
                    }

                    return wrapButtons(html);
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
            title: '卸载库存项',
            fields: {
                location: {
                    icon: 'fa-sitemap',
                    filters: {
                        structural: false,
                    },
                    tree_picker: {
                        url: '/api/stock/location/tree/',
                    },
                },
                note: {
                    icon: 'fa-sticky-note',
                },
            },
            preFormContent: function(opts) {
                var html = '';

                if (installed_item_id == null) {
                    html += `
                    <div class='alert alert-block alert-info'>
                    选择要卸载的库存项
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
        <strong>在此项中安装另一个库存项</strong><br>
        只有满足以下条件，才能安装库存项目:<br>
        <ul>
            <li>库存项链接到一个零件，该零件是此库存项的物料清单</li>
            <li>该库存项目前有库存</li>
            <li>库存项目尚未安装在其他项目中</li>
            <li>库存项被批号或序列号跟踪</li>
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
                    label: '零件',
                    help_text: '选择要安装的零件',
                    model: 'part',
                    api_url: '/api/part/',
                    auto_fill: true,
                    filters: {
                        trackable: true,
                        in_bom_for: options.enforce_bom ? part_id : undefined,
                    }
                },
                stock_item: {
                    filters: {
                        part_detail: true,
                        in_stock: true,
                        tracked: true,
                    },
                    onSelect: function(data, field, opts) {
                        // Adjust the 'quantity' field
                        if ('quantity' in data) {
                            updateFieldValue('quantity', data.quantity, opts);
                        }
                    },
                    adjustFilters: function(filters, opts) {
                        var part = getFormFieldValue('part', {}, opts);

                        if (part) {
                            filters.part = part;
                        }

                        return filters;
                    }
                },
                quantity: {},
            },
            confirm: true,
            title: '安装库存项',
            preFormContent: html,
            onSuccess: function(response) {
                if (options.onSuccess) {
                    options.onSuccess(response);
                }
            }
        }
    );
}

// Perform the specified stock adjustment action against the selected items
function stockAdjustment(action, items, table) {
    adjustStock(action, items, {
        success: function() {
            $(table).bootstrapTable('refresh');
        }
    });
}


/*
 * Set the status of the selected stock items
 */
function setStockStatus(items, options={}) {

    if (items.length == 0) {
        showAlertDialog(
            '选择库存项',
            '选择一个或多个库存项目'
        );
        return;
    }

    let id_values = [];

    items.forEach(function(item) {
        id_values.push(item.pk)
    });

    let html = `
    <div class='alert alert-info alert-block>
    选定的库存项: ${items.length}
    </div>`;

    constructForm('/api/stock/change_status/', {
        title: '更改库存状态',
        method: 'POST',
        preFormContent: html,
        fields: {
            status_custom_key: {},
            note: {},
        },
        processBeforeUpload: function(data) {
            let item_pk_values = [];
            items.forEach(function(item) {
                item_pk_values.push(item.pk);
            });
            data.items = item_pk_values;
            return data;
        },
        onSuccess: function() {
            $(options.table).bootstrapTable('refresh');
        }
    });
}


/*
 * Load TestStatistics table.
 */
function loadTestStatisticsTable(table, prefix, url, options, filters = {}) {
    inventreeGet(url, filters, {
        async: true,
        success: function(data) {
            const keys = ['passed', 'failed', 'total']
            let header = '';
            let rows = []
            let passed= '';
            let failed = '';
            let total = '';
            $('.test-stat-result-cell').remove();
            $.each(data[0], function(key, value){
                if (key != "total") {
                    header += '<th class="test-stat-result-cell">' + key + '</th>';
                    keys.forEach(function(keyName) {
                        var tdText = '-';
                        if (value['total'] != '0' && value[keyName] != '0') {
                            let percentage = ''
                            if (keyName != 'total' && value[total] != 0) {
                                percentage = ' (' + (100.0 * (parseFloat(value[keyName]) / parseFloat(value['total']))).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 2}) + '%)';
                            }
                            tdText = value[keyName] + percentage;
                        }
                        rows[keyName] += '<td class="test-stat-result-cell">' + tdText + '</td>';
                    })
                }
            });
            $('#' + prefix + '-test-statistics-table-header-id').after(header);

            keys.forEach(function(keyName) {
                let valueStr = data[0]['total'][keyName];
                if (keyName != 'total' && data[0]['total']['total'] != '0') {
                    valueStr += ' (' + (100.0 * (parseFloat(valueStr) / parseFloat(data[0]['total']['total']))).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 2}) + '%)';
                }
                rows[keyName] += '<td class="test-stat-result-cell">' + valueStr + '</td>';
                $('#' + prefix + '-test-statistics-table-body-' + keyName).after(rows[keyName]);
            });
            $('#' + prefix + '-test-statistics-table').show();
            setupFilterList(prefix + "teststatistics", table, "#filter-list-" + prefix + "teststatistics", options);
        },
    });
}

function prepareTestStatisticsTable(keyName, apiUrl)
{
    let options = {
        custom_actions: [
            {
                icon: 'fa-calendar-week',
                actions: [
                    {
                        icon: 'fa-calendar-week',
                        title: '本周',
                        label: 'this-week',
                        callback: function(data) {
                            filterTestStatisticsTableDateRange(data, 'this-week', $("#test-statistics-table"), keyName + 'teststatistics', options);
                        }
                    },
                    {
                        icon: 'fa-calendar-week',
                        title: '本月',
                        label: 'this-month',
                        callback: function(data) {
                            filterTestStatisticsTableDateRange(data, 'this-month', $("#test-statistics-table"), keyName + 'teststatistics', options);
                        }
                    },
                ],
            }
        ],
        callback: function(table, filters, options) {
            loadTestStatisticsTable($("#test-statistics-table"), keyName, apiUrl, options, filters);
        }
    }
    setupFilterList(keyName + 'teststatistics', $("#test-statistics-table"), '#filter-list-' + keyName + 'teststatistics', options);

    // Load test statistics table
    loadTestStatisticsTable($("#test-statistics-table"), keyName, apiUrl, options);
}

function filterTestStatisticsTableDateRange(data, range, table, tableKey, options)
{
    var startDateString = '';
    var d = new Date();
    if (range == "this-week") {
        startDateString = moment(new Date(d.getFullYear(), d.getMonth(), d.getDate() - (d.getDay() == 0 ? 6 : d.getDay() - 1))).format('YYYY-MM-DD');
    } else if (range == "this-month") {
        startDateString = moment(new Date(d.getFullYear(), d.getMonth(), 1)).format('YYYY-MM-DD');
    } else {
        console.warn(`Invalid range specified for filterTestStatisticsTableDateRange`);
        return;
    }
    var filters = addTableFilter(tableKey, 'finished_datetime_after', startDateString);
    removeTableFilter(tableKey, 'finished_datetime_before')

    reloadTableFilters(table, filters, options);
    setupFilterList(tableKey, table, "#filter-list-" + tableKey, options);
}
