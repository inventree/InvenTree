



/* globals
    addClearCallback,
    calculateTotalPrice,
    clearEvents,
    companyFormFields,
    constructExpandCollapseButtons,
    constructField,
    constructForm,
    constructOrderTableButtons,
    endDate,
    formatCurrency,
    FullCalendar,
    getFormFieldValue,
    global_settings,
    handleFormErrors,
    handleFormSuccess,
    imageHoverIcon,
    initializeRelatedField,
    inventreeGet,
    inventreeLoad,
    inventreePut,
    launchModalForm,
    locationDetail,
    loadTableFilters,
    makeCopyButton,
    makeEditButton,
    makeDeleteButton,
    makeIconBadge,
    makeIconButton,
    makeProgressBar,
    makeRemoveButton,
    moment,
    newBuildOrder,
    orderParts,
    reloadTotal,
    renderDate,
    renderLink,
    salesOrderStatusDisplay,
    setupFilterList,
    showAlertDialog,
    showApiError,
    startDate,
    thumbnailImage,
    updateFieldValue,
    wrapButtons,
*/

/* exported
    allocateStockToSalesOrder,
    cancelSalesOrder,
    completeSalesOrder,
    completeSalesOrderShipment,
    completePendingShipments,
    createSalesOrder,
    createSalesOrderLineItem,
    createSalesOrderShipment,
    editSalesOrder,
    exportOrder,
    issueSalesOrder,
    loadSalesOrderAllocationTable,
    loadSalesOrderLineItemTable,
    loadSalesOrderShipmentTable,
    loadSalesOrderTable,
    orderParts,
    loadOrderTotal
*/



/*
 * Construct a set of form fields for the SalesOrder model
 */
function salesOrderFields(options={}) {
    let fields = {
        reference: {
            icon: 'fa-hashtag',
        },
        description: {},
        customer: {
            icon: 'fa-user-tie',
            secondary: {
                title: '添加客户',
                fields: function() {
                    var fields = companyFormFields();
                    fields.is_customer.value = true;
                    return fields;
                }
            }
        },
        customer_reference: {},
        project_code: {
            icon: 'fa-list',
        },
        order_currency: {
            icon: 'fa-coins',
        },
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
        address: {
            icon: 'fa-map',
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
            filters: {
                is_active: true,
            }
        }
    };

    if (!global_settings.PROJECT_CODES_ENABLED) {
        delete fields.project_code;
    }

    return fields;
}


/*
 * Create a new SalesOrder
 */
function createSalesOrder(options={}) {

    let fields = salesOrderFields(options);

    if (options.customer) {
        fields.customer.value = options.customer;
    }

    constructForm('/api/order/so/', {
        method: 'POST',
        fields: fields,
        title: '创建销售订单',
        onSuccess: function(data) {
            location.href = `/order/sales-order/${data.pk}/`;
        },
    });
}


/*
 * Edit an existing SalesOrder
 */
function editSalesOrder(order_id, options={}) {

    constructForm(`/api/order/so/${order_id}/`, {
        fields: salesOrderFields(options),
        title: '编辑销售订单',
        onSuccess: function(response) {
            handleFormSuccess(response, options);
        }
    });
}




/* Construct a set of fields for the SalesOrderLineItem form */
function soLineItemFields(options={}) {

    let fields = {
        order: {
            hidden: true,
        },
        part: {
            icon: 'fa-shapes',
        },
        quantity: {},
        reference: {},
        sale_price: {
            icon: 'fa-dollar-sign',
        },
        sale_price_currency: {
            icon: 'fa-coins',
        },
        target_date: {
            icon: 'fa-calendar-alt',
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

    if (options.target_date) {
        fields.target_date.value = options.target_date;
    }

    return fields;
}


/*
 * Launch a modal form to create a new SalesOrderLineItem
 */
function createSalesOrderLineItem(options={}) {

    let fields = soLineItemFields(options);

    constructForm('/api/order/so-line/', {
        fields: fields,
        method: 'POST',
        title: '添加行项目',
        onSuccess: function(response) {
            handleFormSuccess(response, options);
        },
    });
}


/*
 * Form field definitions for a SalesOrderShipment
 */
function salesOrderShipmentFields(options={}) {
    var fields = {
        order: {},
        reference: {},
        tracking_number: {
            icon: 'fa-hashtag',
        },
        invoice_number: {
            icon: 'fa-dollar-sign',
        },
        link: {
            icon: 'fa-link',
        },
        delivery_date: {
            icon: 'fa-calendar-check',
        }
    };

    // If order is specified, hide the order field
    if (options.order) {
        fields.order.value = options.order;
        fields.order.hidden = true;
    }

    return fields;
}


/*
 * Complete a Sales Order shipment
 */
function completeSalesOrderShipment(shipment_id, options={}) {

    // Request the list of stock items which will be shipped
    inventreeGet(`/api/order/so/shipment/${shipment_id}/`, {}, {
        success: function(shipment) {
            var allocations = shipment.allocations;

            var html = '';

            if (!allocations || allocations.length == 0) {
                html = `
                <div class='alert alert-block alert-danger'>
                此装运未分配任何库存物品
                </div>
                `;
            } else {
                html = `
                以下库存商品将发货
                <table class='table table-striped table-condensed'>
                    <thead>
                        <tr>
                            <th>零件</th>
                            <th>庫存品項</th>
                        </tr>
                    </thead>
                    <tbody>
                `;

                allocations.forEach(function(allocation) {

                    var part = allocation.part_detail;
                    var thumb = thumbnailImage(part.thumbnail || part.image);

                    var stock = '';

                    if (allocation.serial) {
                        stock = `序列号: ${allocation.serial}`;
                    } else {
                        stock = `數量: ${allocation.quantity}`;
                    }

                    html += `
                    <tr>
                        <td>${thumb} ${part.full_name}</td>
                        <td>${stock}</td>
                    </tr>
                    `;
                });

                html += `
                    </tbody>
                </table>
                `;
            }

            constructForm(`/api/order/so/shipment/${shipment_id}/ship/`, {
                method: 'POST',
                title: `完成配送 ${shipment.reference}`,
                fields: {
                    shipment_date: {
                        value: moment().format('YYYY-MM-DD'),
                    },
                    tracking_number: {
                        value: shipment.tracking_number,
                        icon: 'fa-hashtag',
                    },
                    invoice_number: {
                        value: shipment.invoice_number,
                        icon: 'fa-dollar-sign',
                    },
                    link: {
                        value: shipment.link,
                        icon: 'fa-link',
                    },
                    delivery_date: {
                        value: shipment.delivery_date,
                        icon: 'fa-calendar-check',
                    },
                },
                preFormContent: html,
                confirm: true,
                confirmMessage: '确认配送',
                buttons: options.buttons,
                onSuccess: function(data) {
                    // Reload tables
                    $('#so-lines-table').bootstrapTable('refresh');
                    $('#pending-shipments-table').bootstrapTable('refresh');
                    $('#completed-shipments-table').bootstrapTable('refresh');

                    if (options.onSuccess instanceof Function) {
                        options.onSuccess(data);
                    }
                },
                reload: options.reload
            });
        }
    });
}

/*
 * Launches a modal to mark all allocated pending shipments as complete
 */
function completePendingShipments(order_id, options={}) {
    var pending_shipments = null;

    // Request the list of stock items which will be shipped
    inventreeGet(`/api/order/so/shipment/`,
        {
            order: order_id,
            shipped: false
        },
        {
            async: false,
            success: function(shipments) {
                pending_shipments = shipments;
            }
        }
    );

    var allocated_shipments = [];

    for (var idx = 0; idx < pending_shipments.length; idx++) {
        if (pending_shipments[idx].allocations.length > 0) {
            allocated_shipments.push(pending_shipments[idx]);
        }
    }

    if (allocated_shipments.length > 0) {
        completePendingShipmentsHelper(allocated_shipments, 0, options);

    } else {
        let html = `
        <div class='alert alert-block alert-danger'>
        `;

        if (!pending_shipments.length) {
            html += `
            未找到待处理的货物
            `;
        } else {
            html += `
            未将库存项目分配给待处理的发货
            `;
        }

        html += `
        </div>
        `;

        constructForm(`/api/order/so/shipment/0/ship/`, {
            method: 'POST',
            title: '完成配送',
            preFormContent: html,
            onSubmit: function(fields, options) {
                handleFormSuccess(fields, options);
            },
            closeText: 'Close',
            hideSubmitButton: true,
        });
    }
}


/*
 * Recursive helper for opening shipment completion modals
 */
function completePendingShipmentsHelper(shipments, shipment_idx, options={}) {
    if (shipment_idx < shipments.length) {
        completeSalesOrderShipment(shipments[shipment_idx].pk,
            {
                buttons: [
                    {
                        name: 'skip',
                        title: `跳过`,
                        onClick: function(form_options) {
                            if (form_options.modal) {
                                $(form_options.modal).modal('hide');
                            }

                            completePendingShipmentsHelper(shipments, shipment_idx + 1, options);
                        }
                    }
                ],
                onSuccess: function(data) {
                    completePendingShipmentsHelper(shipments, shipment_idx + 1, options);
                },
            }
        );

    } else if (options.reload) {
        location.reload();
    }
}



/*
 * Launches a modal form to mark a SalesOrder as "shipped"
 */
function shipSalesOrder(order_id, options={}) {

    constructForm(
        `/api/order/so/${order_id}/complete/`,
        {
            method: 'POST',
            title: '发货销售订单',
            confirm: true,
            fieldsFunction: function(opts) {
                var fields = {
                    accept_incomplete: {},
                };

                if (opts.context.is_complete) {
                    delete fields['accept_incomplete'];
                }

                return fields;
            },
            preFormContent: function(opts) {
                var html = `
                <div class='alert alert-block alert-info'>
                    发送此订单？
                </div>`;

                if (opts.context.pending_shipments) {
                    html += `
                    <div class='alert alert-block alert-danger'>
                    订单无法发货，因为发货不完整<br>
                    </div>`;
                }

                if (!opts.context.is_complete) {
                    html += `
                    <div class='alert alert-block alert-warning'>
                    此订单有未完成的行项目。<br>
                    运送此订单意味着订单和行项目将不再可编辑。
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
 * Launches a modal form to mark a SalesOrder as "completed"
 */
function completeSalesOrder(order_id, options={}) {

    constructForm(
        `/api/order/so/${order_id}/complete/`,
        {
            method: 'POST',
            title: '完成销售订单',
            confirm: true,
            fieldsFunction: function(opts) {
                var fields = {
                    accept_incomplete: {},
                };

                if (opts.context.is_complete) {
                    delete fields['accept_incomplete'];
                }

                return fields;
            },
            preFormContent: function(opts) {
                var html = `
                <div class='alert alert-block alert-info'>
                    标记该订单为已完成？
                </div>`;

                return html;
            },
            onSuccess: function(response) {
                handleFormSuccess(response, options);
            }
        }
    );
}


/*
 * Launches sa modal form to mark a SalesOrder as "issued"
 */
function issueSalesOrder(order_id, options={}) {

    let html = `
    <div class='alert alert-block alert-info'>
    发出此销售订单？
    </div>`;

    constructForm(`/api/order/so/${order_id}/issue/`, {
        method: 'POST',
        title: '发出销售订单',
        confirm: true,
        preFormContent: html,
        onSuccess: function(response) {
            handleFormSuccess(response, options);
        }
    });
}


/*
 * Launches a modal form to mark a SalesOrder as "cancelled"
 */
function cancelSalesOrder(order_id, options={}) {

    constructForm(
        `/api/order/so/${order_id}/cancel/`,
        {
            method: 'POST',
            title: '取消销售订单',
            confirm: true,
            preFormContent: function(opts) {
                var html = `
                <div class='alert alert-block alert-warning'>
                取消此订单意味着订单将不再可编辑。
                </div>`;

                return html;
            },
            onSuccess: function(response) {
                handleFormSuccess(response, options);
            }
        }
    );
}

// Open a dialog to create a new sales order shipment
function createSalesOrderShipment(options={}) {

    // Work out the next shipment number for the given order
    inventreeGet(
        '/api/order/so/shipment/',
        {
            order: options.order,
        },
        {
            success: function(results) {
                // "predict" the next reference number
                var ref = results.length + 1;

                var found = false;

                while (!found) {

                    var no_match = true;

                    for (var ii = 0; ii < results.length; ii++) {
                        if (ref.toString() == results[ii].reference.toString()) {
                            no_match = false;
                            break;
                        }
                    }

                    if (no_match) {
                        break;
                    } else {
                        ref++;
                    }
                }

                var fields = salesOrderShipmentFields(options);

                fields.reference.value = ref;
                fields.reference.prefix = options.reference;

                constructForm('/api/order/so/shipment/', {
                    method: 'POST',
                    fields: fields,
                    title: '创建新的配送',
                    onSuccess: function(data) {
                        if (options.onSuccess) {
                            options.onSuccess(data);
                        }
                    }
                });
            }
        }
    );
}



/*
 * Load table displaying list of sales orders
 */
function loadSalesOrderTable(table, options) {

    // Ensure the table starts in a known state
    $(table).bootstrapTable('destroy');

    options.params = options.params || {};
    options.params['customer_detail'] = true;

    var filters = loadTableFilters('salesorder', options.params);

    setupFilterList('salesorder', $(table), '#filter-list-salesorder', {
        download: true,
        report: {
            key: 'salesorder'
        }
    });

    var display_mode = inventreeLoad('salesorder-table-display-mode', 'list');

    function buildEvents(calendar) {

        var start = startDate(calendar);
        var end = endDate(calendar);

        clearEvents(calendar);

        // Extract current filters from table
        var table_options = $(table).bootstrapTable('getOptions');
        var filters = table_options.query_params || {};

        filters.customer_detail = true;
        filters.min_date = start;
        filters.max_date = end;

        // Request orders from the server within specified date range
        inventreeGet(
            '/api/order/so/',
            filters,
            {
                success: function(response) {

                    for (var idx = 0; idx < response.length; idx++) {
                        var order = response[idx];

                        var date = order.creation_date;

                        if (order.shipment_date) {
                            date = order.shipment_date;
                        } else if (order.target_date) {
                            date = order.target_date;
                        }

                        var title = `${order.reference} - ${order.customer_detail.name}`;

                        // Default color is blue
                        var color = '#4c68f5';

                        // Overdue orders are red
                        if (order.overdue) {
                            color = '#c22525';
                        } else if (order.status == 20) {
                            color = '#25c235';
                        }

                        var event = {
                            title: title,
                            start: date,
                            end: date,
                            url: `/order/sales-order/${order.pk}/`,
                            backgroundColor: color,
                        };

                        calendar.addEvent(event);
                    }
                }
            }
        );
    }

    $(table).inventreeTable({
        url: '/api/order/so/',
        queryParams: filters,
        name: 'salesorder',
        groupBy: false,
        sidePagination: 'server',
        original: options.params,
        showColums: display_mode != 'calendar',
        search: display_mode != 'calendar',
        showCustomViewButton: false,
        showCustomView: display_mode == 'calendar',
        disablePagination: display_mode == 'calendar',
        formatNoMatches: function() {
            return '未找到销售订单';
        },
        buttons: constructOrderTableButtons({
            prefix: 'salesorder',
            disableTreeView: true,
            callback: function() {
                // Reload the entire table
                loadSalesOrderTable(table, options);
            },
        }),
        customView: function(data) {
            return `<div id='purchase-order-calendar'></div>`;
        },
        onLoadSuccess: function() {

            if (display_mode == 'calendar') {
                var el = document.getElementById('purchase-order-calendar');

                let calendar = new FullCalendar.Calendar(el, {
                    initialView: 'dayGridMonth',
                    nowIndicator: true,
                    aspectRatio: 2.5,
                    locale: options.locale,
                    datesSet: function() {
                        buildEvents(calendar);
                    }
                });

                calendar.render();
            }
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
                title: '销售订单',
                formatter: function(value, row) {
                    var html = renderLink(value, `/order/sales-order/${row.pk}/`);

                    if (row.overdue) {
                        html += makeIconBadge('fa-calendar-times icon-red', '订单已逾期');
                    }

                    return html;
                },
            },
            {
                sortable: true,
                sortName: 'customer__name',
                field: 'customer_detail',
                title: '客户',
                formatter: function(value, row) {

                    if (!row.customer_detail) {
                        return '无效的客户';
                    }

                    return imageHoverIcon(row.customer_detail.image) + renderLink(row.customer_detail.name, `/company/${row.customer}/?display=sales-orders/`);
                }
            },
            {
                sortable: true,
                field: 'customer_reference',
                title: '客户参考',
            },
            {
                sortable: false,
                field: 'description',
                title: '描述',
            },
            {
                field: 'project_code',
                title: '專案代碼',
                switchable: global_settings.PROJECT_CODES_ENABLED,
                visible: global_settings.PROJECT_CODES_ENABLED,
                sortable: true,
                formatter: function(value, row) {
                    if (row.project_code_detail) {
                        return `<span title='${row.project_code_detail.description}'>${row.project_code_detail.code}</span>`;
                    }
                }
            },
            {
                sortable: true,
                field: 'status_custom_key',
                title: '狀態',
                formatter: function(value, row) {
                    return salesOrderStatusDisplay(row.status_custom_key);
                }
            },
            {
                sortable: true,
                field: 'creation_date',
                title: '建立日期',
                formatter: function(value) {
                    return renderDate(value);
                }
            },
            {
                sortable: true,
                field: 'target_date',
                title: '预计日期',
                formatter: function(value) {
                    return renderDate(value);
                }
            },
            {
                sortable: true,
                field: 'shipment_date',
                title: '发货日期',
                formatter: function(value) {
                    return renderDate(value);
                }
            },
            {
                sortable: true,
                field: 'line_items',
                title: '项目'
            },
            {
                field: 'total_price',
                title: '总成本',
                switchable: true,
                sortable: true,
                formatter: function(value, row) {
                    return formatCurrency(value, {
                        currency: row.order_currency ?? row.customer_detail?.currency,
                    });
                }
            }
        ],
    });
}


/*
 * Load a table displaying Shipment information against a particular order
 */
function loadSalesOrderShipmentTable(table, options={}) {

    options.table = table;

    options.params = options.params || {};

    // Filter by order
    options.params.order = options.order;

    // Filter by "shipped" status
    options.params.shipped = options.shipped || false;

    var filters = loadTableFilters('salesordershipment', options.params);

    setupFilterList('salesordershipment', $(table), options.filter_target);

    // Add callbacks for expand / collapse buttons
    var prefix = options.shipped ? 'completed' : 'pending';

    // Add option to show SO reference also
    var show_so_reference = options.show_so_reference || false;

    $(`#${prefix}-shipments-expand`).click(function() {
        $(table).bootstrapTable('expandAllRows');
    });

    $(`#${prefix}-shipments-collapse`).click(function() {
        $(table).bootstrapTable('collapseAllRows');
    });

    function makeShipmentActions(row) {
        // Construct "actions" for the given shipment row
        var pk = row.pk;

        let html = '';

        html += makeEditButton('button-shipment-edit', pk, '编辑配送');

        if (!options.shipped) {
            html += makeIconButton('fa-truck icon-green', 'button-shipment-ship', pk, '完成配送');
        }

        var enable_delete = row.allocations && row.allocations.length == 0;

        html += makeDeleteButton('button-shipment-delete', pk, '删除配送', {disabled: !enable_delete});

        return wrapButtons(html);
    }

    function setupShipmentCallbacks() {
        // Setup action button callbacks

        $(table).find('.button-shipment-edit').click(function() {
            var pk = $(this).attr('pk');

            var fields = salesOrderShipmentFields();

            delete fields.order;

            constructForm(`/api/order/so/shipment/${pk}/`, {
                fields: fields,
                title: '编辑配送',
                refreshTable: table,
            });
        });

        $(table).find('.button-shipment-ship').click(function() {
            var pk = $(this).attr('pk');

            completeSalesOrderShipment(pk);
        });

        $(table).find('.button-shipment-delete').click(function() {
            var pk = $(this).attr('pk');

            constructForm(`/api/order/so/shipment/${pk}/`, {
                title: '删除配送',
                method: 'DELETE',
                refreshTable: table,
            });
        });
    }

    $(table).inventreeTable({
        url: '/api/order/so/shipment/',
        queryParams: filters,
        original: options.params,
        name: options.name || 'salesordershipment',
        search: false,
        paginationVAlign: 'bottom',
        showColumns: true,
        detailView: true,
        detailViewByClick: false,
        buttons: constructExpandCollapseButtons(table),
        detailFilter: function(index, row) {
            return row.allocations.length > 0;
        },
        detailFormatter: function(index, row, element) {
            return showAllocationSubTable(index, row, element, options);
        },
        onPostBody: function() {
            setupShipmentCallbacks();

            // Auto-expand rows on the "pending" table
            if (!options.shipped) {
                $(table).bootstrapTable('expandAllRows');
            }
        },
        formatNoMatches: function() {
            return '未找到匹配的货物';
        },
        columns: [
            {
                visible: false,
                checkbox: true,
                switchable: false,
            },
            {
                visible: show_so_reference,
                field: 'order_detail',
                title: '销售订单',
                switchable: false,
                formatter: function(value, row) {
                    var html = renderLink(row.order_detail.reference, `/order/sales-order/${row.order}/`);

                    if (row.overdue) {
                        html += makeIconBadge('fa-calendar-times icon-red', '订单已逾期');
                    }

                    return html;
                },
            },
            {
                field: 'reference',
                title: '配送参考',
                switchable: false,
            },
            {
                field: 'allocations',
                title: '项目',
                switchable: false,
                sortable: true,
                formatter: function(value, row) {
                    if (row && row.allocations) {
                        return row.allocations.length;
                    } else {
                        return '-';
                    }
                }
            },
            {
                field: 'shipment_date',
                title: '发货日期',
                sortable: true,
                formatter: function(value, row) {
                    if (value) {
                        return renderDate(value);
                    } else {
                        return '<em>未配送</em>';
                    }
                }
            },
            {
                field: 'delivery_date',
                title: '送达日期',
                sortable: true,
                formatter: function(value, row) {
                    if (value) {
                        return renderDate(value);
                    } else {
                        return '<em>未知</em>';
                    }
                }
            },
            {
                field: 'tracking_number',
                title: '追踪',
            },
            {
                field: 'invoice_number',
                title: '发票',
            },
            {
                field: 'link',
                title: '連結',
                formatter: function(value) {
                    if (value) {
                        return renderLink(value, value);
                    } else {
                        return '-';
                    }
                }
            },
            {
                field: 'notes',
                title: '备注',
                visible: false,
                switchable: false,
                // TODO: Implement 'notes' field
            },
            {
                title: '',
                switchable: false,
                formatter: function(value, row) {
                    return makeShipmentActions(row);
                }
            }
        ],
    });
}


/**
 * Allocate stock items against a SalesOrder
 *
 * arguments:
 * - order_id: The ID / PK value for the SalesOrder
 * - lines: A list of SalesOrderLineItem objects to be allocated
 *
 * options:
 *  - source_location: ID / PK of the top-level StockLocation to source stock from (or null)
 */
function allocateStockToSalesOrder(order_id, line_items, options={}) {

    function renderLineItemRow(line_item, quantity) {
        // Function to render a single line_item row

        var pk = line_item.pk;

        var part = line_item.part_detail;

        var thumb = thumbnailImage(part.thumbnail || part.image);

        let delete_button = wrapButtons(
            makeRemoveButton(
                'button-row-remove',
                pk,
                '移除行',
            )
        );

        delete_button += '</div>';

        var quantity_input = constructField(
            `items_quantity_${pk}`,
            {
                type: 'decimal',
                min_value: 0,
                value: quantity || 0,
                title: '指定库存分配数量',
                required: true,
            },
            {
                hideLabels: true,
            }
        );

        var stock_input = constructField(
            `items_stock_item_${pk}`,
            {
                type: 'related field',
                required: 'true',
            },
            {
                hideLabels: true,
            }
        );

        var html = `
        <tr id='allocation_row_${pk}' class='line-allocation-row'>
            <td id='part_${pk}'>
                ${thumb} ${part.full_name}
            </td>
            <td id='stock_item_${pk}'>
                ${stock_input}
            </td>
            <td id='quantity_${pk}'>
                ${quantity_input}
            </td>
            <td id='buttons_${pk}>
                ${delete_button}
            </td>
        </tr>
        `;

        return html;
    }

    var table_entries = '';

    for (var idx = 0; idx < line_items.length; idx++ ) {
        let line_item = line_items[idx];
        let remaining = Math.max(0, line_item.quantity - line_item.allocated);

        table_entries += renderLineItemRow(line_item, remaining);
    }

    if (table_entries.length == 0) {
        showAlertDialog(
            '选择零件',
            '您必须选择至少一个要分配的零件',
        );

        return;
    }

    var html = '';

    // Render a "source location" input field
    html += constructField(
        'take_from',
        {
            type: 'related field',
            label: '來源倉儲地點',
            help_text: '选择源位置 (留空以从所有位置取出)',
            required: false,
        },
        {},
    );

    // Create table of line items
    html += `
    <table class='table table-striped table-condensed' id='stock-allocation-table'>
        <thead>
            <tr>
                <th>零件</th>
                <th style='min-width: 250px;'>庫存品項</th>
                <th>數量</th>
                <th></th>
        </thead>
        <tbody>
            ${table_entries}
        </tbody>
    </table>`;

    constructForm(`/api/order/so/${order_id}/allocate/`, {
        method: 'POST',
        fields: {
            shipment: {
                filters: {
                    order: order_id,
                    shipped: false,
                },
                value: options.shipment || null,
                auto_fill: true,
                secondary: {
                    method: 'POST',
                    title: '添加配送',
                    fields: function() {
                        var ref = null;

                        // TODO: Refactor code for getting next shipment number
                        inventreeGet(
                            '/api/order/so/shipment/',
                            {
                                order: options.order,
                            },
                            {
                                async: false,
                                success: function(results) {
                                    // "predict" the next reference number
                                    ref = results.length + 1;

                                    var found = false;

                                    while (!found) {

                                        var no_match = true;

                                        for (var ii = 0; ii < results.length; ii++) {
                                            if (ref.toString() == results[ii].reference.toString()) {
                                                no_match = false;
                                                break;
                                            }
                                        }

                                        if (no_match) {
                                            break;
                                        } else {
                                            ref++;
                                        }
                                    }
                                }
                            }
                        );

                        var fields = salesOrderShipmentFields(options);

                        fields.reference.value = ref;
                        fields.reference.prefix = options.reference;

                        return fields;
                    }
                }
            }
        },
        preFormContent: html,
        confirm: true,
        confirmMessage: '确认库存分配',
        title: '分配库存项到销售订单',
        afterRender: function(fields, opts) {

            // Initialize source location field
            var take_from_field = {
                name: 'take_from',
                model: 'stocklocation',
                api_url: '/api/stock/location/',
                required: false,
                type: 'related field',
                value: options.source_location || null,
                noResults: function(query) {
                    return '没有匹配的库存位置';
                },
            };

            initializeRelatedField(
                take_from_field,
                null,
                opts
            );

            // Add callback to "clear" button for take_from field
            addClearCallback(
                'take_from',
                take_from_field,
                opts,
            );

            // Initialize fields for each line item
            line_items.forEach(function(line_item) {
                var pk = line_item.pk;

                initializeRelatedField(
                    {
                        name: `items_stock_item_${pk}`,
                        api_url: '/api/stock/',
                        filters: {
                            part: line_item.part,
                            in_stock: true,
                            part_detail: true,
                            location_detail: true,
                            available: true,
                            salable: true,
                            active: true,
                        },
                        model: 'stockitem',
                        required: true,
                        render_part_detail: true,
                        render_location_detail: true,
                        auto_fill: true,
                        onSelect: function(data, field, opts) {
                            // Adjust the 'quantity' field based on availability

                            if (!('quantity' in data)) {
                                return;
                            }

                            // Calculate the available quantity
                            var available = Math.max((data.quantity || 0) - (data.allocated || 0), 0);

                            // Remaining quantity to be allocated?
                            var remaining = Math.max(line_item.quantity - line_item.allocated, 0);

                            // Maximum amount that we need
                            var desired = Math.min(available, remaining);

                            updateFieldValue(`items_quantity_${pk}`, desired, {}, opts);

                        },
                        adjustFilters: function(filters) {
                            // Restrict query to the selected location
                            var location = getFormFieldValue(
                                'take_from',
                                {},
                                {
                                    modal: opts.modal,
                                }
                            );

                            filters.location = location;
                            filters.cascade = true;

                            // Exclude expired stock?
                            if (global_settings.STOCK_ENABLE_EXPIRY && !global_settings.STOCK_ALLOW_EXPIRED_SALE) {
                                filters.expired = false;
                            }

                            return filters;
                        },
                        noResults: function(query) {
                            return '没有匹配的库存项';
                        }
                    },
                    null,
                    opts
                );
            });

            // Add remove-row button callbacks
            $(opts.modal).find('.button-row-remove').click(function() {
                var pk = $(this).attr('pk');

                $(opts.modal).find(`#allocation_row_${pk}`).remove();
            });
        },
        onSubmit: function(fields, opts) {
            // Extract data elements from the form
            var data = {
                items: [],
                shipment: getFormFieldValue(
                    'shipment',
                    {},
                    opts
                )
            };

            var item_pk_values = [];

            line_items.forEach(function(item) {

                var pk = item.pk;

                var quantity = getFormFieldValue(
                    `items_quantity_${pk}`,
                    {},
                    opts
                );

                var stock_item = getFormFieldValue(
                    `items_stock_item_${pk}`,
                    {},
                    opts
                );

                if (quantity != null) {
                    data.items.push({
                        line_item: pk,
                        stock_item: stock_item,
                        quantity: quantity,
                    });

                    item_pk_values.push(pk);
                }
            });

            // Provide nested values
            opts.nested = {
                'items': item_pk_values
            };

            inventreePut(
                opts.url,
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
                            showApiError(xhr);
                            break;
                        }
                    }
                }
            );
        },
    });
}


/**
 * Load a table with SalesOrderAllocation items
 */
function loadSalesOrderAllocationTable(table, options={}) {

    options.params = options.params || {};

    options.params['location_detail'] = true;
    options.params['part_detail'] = true;
    options.params['item_detail'] = true;
    options.params['order_detail'] = true;

    let filters = loadTableFilters('salesorderallocation', options.params);

    setupFilterList('salesorderallocation', $(table));

    $(table).inventreeTable({
        url: '/api/order/so-allocation/',
        queryParams: filters,
        name: options.name || 'salesorderallocation',
        groupBy: false,
        search: false,
        paginationVAlign: 'bottom',
        original: options.params,
        formatNoMatches: function() {
            return '未找到销售订单分配';
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
                title: '订单',
                formatter: function(value, row) {

                    var ref = `${row.order_detail.reference}`;

                    return renderLink(ref, `/order/sales-order/${row.order}/`);
                }
            },
            {
                field: 'item',
                switchable: false,
                title: '庫存品項',
                formatter: function(value, row) {
                    // Render a link to the particular stock item

                    var link = `/stock/item/${row.item}/`;
                    var text = `庫存品項 ${row.item}`;

                    return renderLink(text, link);
                }
            },
            {
                field: 'location',
                title: '地點',
                formatter: function(value, row) {
                    return locationDetail(row.item_detail, true);
                }
            },
            {
                field: 'quantity',
                title: '數量',
                sortable: true,
            },
            {
                field: 'shipment_date',
                title: '已配送',
                sortable: true,
                formatter: function(value, row) {
                    if (value) {
                        return renderDate(value);
                    } else {
                        return `<em>未配送</em>`;
                    }
                }
            }
        ]
    });
}


/**
 * Display an "allocations" sub table, showing stock items allocated against a sales order
 * @param {*} index
 * @param {*} row
 * @param {*} element
 */
function showAllocationSubTable(index, row, element, options) {

    // Construct a sub-table element
    var html = `
    <div class='sub-table'>
        <table class='table table-striped table-condensed' id='allocation-table-${row.pk}'></table>
    </div>`;

    element.html(html);

    var table = $(`#allocation-table-${row.pk}`);

    function setupCallbacks() {
        // Add callbacks for 'edit' buttons
        table.find('.button-allocation-edit').click(function() {

            var pk = $(this).attr('pk');

            // Edit the sales order allocation
            constructForm(
                `/api/order/so-allocation/${pk}/`,
                {
                    fields: {
                        quantity: {},
                    },
                    title: '编辑库存分配',
                    refreshTable: options.table,
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
                    confirmMessage: '确认删除操作',
                    title: '删除库存分配',
                    refreshTable: options.table,
                }
            );
        });
    }

    table.bootstrapTable({
        onPostBody: setupCallbacks,
        data: row.allocations,
        showHeader: true,
        columns: [
            {
                field: 'part_detail',
                title: '零件',
                formatter: function(part, row) {
                    return imageHoverIcon(part.thumbnail) + renderLink(part.full_name, `/part/${part.pk}/`);
                }
            },
            {
                field: 'allocated',
                title: '庫存品項',
                formatter: function(value, row, index, field) {
                    let item = row.item_detail;
                    let text = `數量: ${row.quantity}`;

                    if (item && item.serial != null && row.quantity == 1) {
                        text = `序列号: ${item.serial}`;
                    }

                    return renderLink(text, `/stock/item/${row.item}/`);
                },
            },
            {
                field: 'location',
                title: '地點',
                formatter: function(value, row, index, field) {

                    if (row.shipment_date) {
                        return `<em>已配送到客户 - ${row.shipment_date}</em>`;
                    } else if (row.location) {
                        // Location specified
                        return renderLink(
                            row.location_detail.pathstring || '地點',
                            `/stock/location/${row.location}/`
                        );
                    } else {
                        return `<em>未指定库存地点</em>`;
                    }
                },
            },
            {
                field: 'buttons',
                title: '',
                formatter: function(value, row, index, field) {

                    let html = '';
                    let pk = row.pk;

                    if (row.shipment_date) {
                        html += `<span class='badge bg-success badge-right'>已配送</span>`;
                    } else {
                        html += makeEditButton('button-allocation-edit', pk, '编辑库存分配');
                        html += makeDeleteButton('button-allocation-delete', pk, '删除库存分配');
                    }

                    return wrapButtons(html);
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
        url: '/api/stock/',
        queryParams: {
            part: row.part,
            sales_order: options.order,
            location_detail: true,
        },
        showHeader: true,
        columns: [
            {
                field: 'pk',
                visible: false,
            },
            {
                field: 'stock',
                title: '庫存品項',
                formatter: function(value, row) {
                    var text = '';
                    if (row.serial && row.quantity == 1) {
                        text = `序列号: ${row.serial}`;
                    } else {
                        text = `數量: ${row.quantity}`;
                    }

                    return renderLink(text, `/stock/item/${row.pk}/`);
                },
            },
            {
                field: 'location',
                title: '地點',
                formatter: function(value, row) {
                    if (row.customer) {
                        return renderLink(
                            '已配送到客户',
                            `/company/${row.customer}/`
                        );
                    } else if (row.location && row.location_detail) {
                        return renderLink(
                            row.location_detail.pathstring,
                            `/stock/location/${row.location}`,
                        );
                    } else {
                        return `<em>未指定库存地点</em>`;
                    }
                }
            }
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
        console.error('loadSalesOrderLineItemTable called without order ID');
        return;
    }

    if (!options.status) {
        console.error('loadSalesOrderLineItemTable called without order status');
        return;
    }

    options.params.order = options.order;
    options.params.part_detail = true;
    options.params.allocations = true;

    var filters = loadTableFilters('salesorderlineitem', options.params);

    options.url = options.url || '/api/order/so-line/';

    var filter_target = options.filter_target || '#filter-list-sales-order-lines';

    setupFilterList(
        'salesorderlineitem',
        $(table),
        filter_target,
        {
            download: true,
        }
    );

    var show_detail = true;

    // Add callbacks for expand / collapse buttons
    $('#sales-lines-expand').click(function() {
        $(table).bootstrapTable('expandAllRows');
    });

    $('#sales-lines-collapse').click(function() {
        $(table).bootstrapTable('collapseAllRows');
    });

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
            sortName: 'part_detail.name',
            field: 'part',
            title: '零件',
            switchable: false,
            formatter: function(value, row, index, field) {
                if (row.part_detail) {
                    return imageHoverIcon(row.part_detail.thumbnail) + renderLink(row.part_detail.full_name, `/part/${value}/`);
                } else {
                    return '-';
                }
            },
            footerFormatter: function() {
                return '总计';
            },
        },
        {
            sortable: false,
            field: 'part_detail.description',
            title: '描述',
            switchable: true,
        },
        {
            sortable: true,
            field: 'reference',
            title: '參考代號',
            switchable: true,
        },
        {
            sortable: true,
            field: 'quantity',
            title: '數量',
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
            title: '单位价格',
            formatter: function(value, row) {
                return formatCurrency(row.sale_price, {
                    currency: row.sale_price_currency
                });
            }
        },
        {
            field: 'total_price',
            sortable: true,
            title: '总价格',
            formatter: function(value, row) {
                return formatCurrency(row.sale_price * row.quantity, {
                    currency: row.sale_price_currency,
                });
            },
            footerFormatter: function(data) {
                return calculateTotalPrice(
                    data,
                    function(row) {
                        return row.sale_price ? row.sale_price * row.quantity : null;
                    },
                    function(row) {
                        return row.sale_price_currency;
                    }
                );
            }
        },
        {
            field: 'target_date',
            title: '预计日期',
            sortable: true,
            switchable: true,
            formatter: function(value, row) {
                if (row.target_date) {
                    var html = renderDate(row.target_date);

                    if (row.overdue) {
                        html += makeIconBadge('fa-calendar-times', '此行项目已逾期');
                    }

                    return html;

                } else if (row.order_detail && row.order_detail.target_date) {
                    return `<em>${renderDate(row.order_detail.target_date)}</em>`;
                } else {
                    return '-';
                }
            }
        }
    ];

    if (options.open) {
        columns.push(
            {
                field: 'stock',
                title: '可用库存',
                formatter: function(value, row) {

                    let available = row.available_stock + row.available_variant_stock;
                    let required = Math.max(row.quantity - row.allocated - row.shipped, 0);

                    let html = '';

                    if (available > 0) {
                        let url = `/part/${row.part}/?display=part-stock`;

                        html = renderLink(available, url);

                        if (row.available_variant_stock && row.available_variant_stock > 0) {
                            html += makeIconBadge('fa-info-circle icon-blue', '包括变体库存');
                        }
                    } else {
                        html += `<span class='badge rounded-pill bg-danger'>无可用库存</span>`;
                    }

                    if (required > 0) {
                        if (available >= required) {
                            html += makeIconBadge('fa-check-circle icon-green', '充足的库存');
                        } else {
                            html += makeIconBadge('fa-times-circle icon-red', '可用库存不足');
                        }
                    }

                    return html;
                },
            },
        );

        columns.push(
            {
                field: 'allocated',
                title: '已分配',
                switchable: false,
                sortable: true,
                formatter: function(value, row, index, field) {
                    return makeProgressBar(row.allocated, row.quantity, {
                        id: `order-line-progress-${row.pk}`,
                    });
                },
                sorter: function(valA, valB, rowA, rowB) {

                    var A = rowA.allocated;
                    var B = rowB.allocated;

                    if (A == 0 && B == 0) {
                        return (rowA.quantity > rowB.quantity) ? 1 : -1;
                    }

                    var progressA = parseFloat(A) / rowA.quantity;
                    var progressB = parseFloat(B) / rowB.quantity;

                    return (progressA < progressB) ? 1 : -1;
                }
            },
        );
    }

    columns.push({
        field: 'shipped',
        title: '已配送',
        switchable: false,
        sortable: true,
        formatter: function(value, row) {
            return makeProgressBar(row.shipped, row.quantity, {
                id: `order-line-shipped-${row.pk}`
            });
        },
        sorter: function(valA, valB, rowA, rowB) {
            var A = rowA.shipped;
            var B = rowB.shipped;

            if (A == 0 && B == 0) {
                return (rowA.quantity > rowB.quantity) ? 1 : -1;
            }

            var progressA = parseFloat(A) / rowA.quantity;
            var progressB = parseFloat(B) / rowB.quantity;

            return (progressA < progressB) ? 1 : -1;
        }
    });

    columns.push({
        field: 'notes',
        title: '备注',
    });

    columns.push({
        field: 'link',
        title: '連結',
        formatter: function(value) {
            if (value) {
                return renderLink(value, value);
            }
        }
    });

    columns.push({
        field: 'buttons',
        switchable: false,
        formatter: function(value, row, index, field) {
            let pk = row.pk;
            let buttons = '';

            // Construct a set of buttons to display
            if (row.part && row.part_detail) {
                let part = row.part_detail;

                if (options.allow_edit && (row.shipped < row.quantity)) {
                    if (part.trackable) {
                        buttons += makeIconButton('fa-hashtag icon-green', 'button-add-by-sn', pk, '分配序列号');
                    }
                    buttons += makeIconButton('fa-sign-in-alt icon-green', 'button-add', pk, '分配库存');
                    if (part.purchaseable) {
                        buttons += makeIconButton('fa-shopping-cart', 'button-buy', row.part, '采购库存');
                    }

                    if (part.assembly) {
                        buttons += makeIconButton('fa-tools', 'button-build', row.part, '生产库存');
                    }
                }
            }

            buttons += makeIconButton('fa-dollar-sign icon-green', 'button-price', pk, '计算价格');

            if (options.allow_edit) {
                buttons += makeCopyButton('button-duplicate', pk, '复制行项目');
                buttons += makeEditButton('button-edit', pk, '编辑行项目');
            }

            if (options.allow_delete) {
                var delete_disabled = false;

                var title = '删除行项目';

                if (row.shipped) {
                    delete_disabled = true;
                    title = '无法删除，因为物品已发货';
                } else if (row.allocated) {
                    delete_disabled = true;
                    title = '无法删除，因为项目已分配';
                }

                // Prevent deletion of the line item if items have been allocated or shipped!
                buttons += makeDeleteButton('button-delete', pk, title, {disabled: delete_disabled});
            }

            return wrapButtons(buttons);
        }
    });

    function reloadTable() {
        $(table).bootstrapTable('refresh');
        reloadTotal();
    }

    // Configure callback functions once the table is loaded
    function setupCallbacks() {

        // Callback for duplicating line items
        $(table).find('.button-duplicate').click(function() {
            var pk = $(this).attr('pk');

            inventreeGet(`/api/order/so-line/${pk}/`, {}, {
                success: function(data) {

                    let fields = soLineItemFields();

                    constructForm('/api/order/so-line/', {
                        method: 'POST',
                        fields: fields,
                        data: data,
                        title: '复制行项目',
                        refreshTable: table,
                    });
                }
            });
        });

        // Callback for editing line items
        $(table).find('.button-edit').click(function() {
            var pk = $(this).attr('pk');

            constructForm(`/api/order/so-line/${pk}/`, {
                fields: soLineItemFields(),
                title: '编辑行项目',
                onSuccess: reloadTable,
            });
        });

        // Callback for deleting line items
        $(table).find('.button-delete').click(function() {
            var pk = $(this).attr('pk');

            constructForm(`/api/order/so-line/${pk}/`, {
                method: 'DELETE',
                title: '删除行项目',
                onSuccess: reloadTable,
            });
        });

        // Callback for allocating stock items by serial number
        $(table).find('.button-add-by-sn').click(function() {
            var pk = $(this).attr('pk');

            inventreeGet(`/api/order/so-line/${pk}/`, {},
                {
                    success: function(response) {

                        constructForm(`/api/order/so/${options.order}/allocate-serials/`, {
                            method: 'POST',
                            title: '分配序列号',
                            fields: {
                                line_item: {
                                    value: pk,
                                    hidden: true,
                                },
                                quantity: {},
                                serial_numbers: {},
                                shipment: {
                                    filters: {
                                        order: options.order,
                                        shipped: false,
                                    },
                                    auto_fill: true,
                                }
                            },
                            refreshTable: table,
                        });
                    }
                }
            );
        });

        // Callback for allocation stock items to the order
        $(table).find('.button-add').click(function() {
            var pk = $(this).attr('pk');

            var line_item = $(table).bootstrapTable('getRowByUniqueId', pk);

            allocateStockToSalesOrder(
                options.order,
                [
                    line_item
                ],
                {
                    order: options.order,
                    reference: options.reference,
                    success: function() {
                        // Reload this table
                        $(table).bootstrapTable('refresh');

                        // Reload the pending shipment table
                        $('#pending-shipments-table').bootstrapTable('refresh');
                    }
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
                success: reloadTable,
                ...options
            });
        });

        // Callback for purchasing parts
        $(table).find('.button-buy').click(function() {
            var pk = $(this).attr('pk');

            inventreeGet(
                `/api/part/${pk}/`,
                {},
                {
                    success: function(part) {
                        orderParts(
                            [part],
                            {}
                        );
                    }
                }
            );
        });

        // Callback for displaying price
        $(table).find('.button-price').click(function() {
            var pk = $(this).attr('pk');
            var idx = $(this).closest('tr').attr('data-index');
            var row = $(table).bootstrapTable('getData')[idx];

            launchModalForm(
                '/order/purchase-order/pricing/',
                {
                    submit_text: '计算价格',
                    data: {
                        line_item: pk,
                        quantity: row.quantity,
                    },
                    buttons: [
                        {
                            name: 'update_price',
                            title: '更新单位价格'
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
        sidePagination: 'client',
        formatNoMatches: function() {
            return '未找到匹配的行项目';
        },
        queryParams: filters,
        original: options.params,
        url: options.url,
        showFooter: true,
        uniqueId: 'pk',
        detailView: show_detail,
        detailViewByClick: false,
        buttons: constructExpandCollapseButtons(table),
        detailFilter: function(index, row) {
            if (options.open) {
                // Order is pending
                return row.allocated > 0;
            } else {
                return row.shipped > 0;
            }
        },
        detailFormatter: function(index, row, element) {
            if (options.open) {
                return showAllocationSubTable(index, row, element, options);
            } else {
                return showFulfilledSubTable(index, row, element, options);
            }
        },
        columns: columns,
    });
}
