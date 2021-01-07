{% load i18n %}
{% load inventree_extras %}
{% load status_codes %}

/* Stock API functions
 * Requires api.js to be loaded first
 */

/* Functions for interacting with stock management forms
 */

function removeStockRow(e) {
    // Remove a selected row from a stock modal form

    e = e || window.event;
    var src = e.target || e.srcElement;

    var row = $(src).attr('row');

    $('#' + row).remove();
}


function passFailBadge(result) {

    if (result) {
        return `<span class='label label-green float-right'>{% trans "PASS" %}</span>`;
    } else {
        return `<span class='label label-red float-right'>{% trans "FAIL" %}</span>`;
    }
}

function noResultBadge() {
    return `<span class='label label-blue float-right'>{% trans "NO RESULT" %}</span>`;
}

function loadStockTestResultsTable(table, options) {
    /*
     * Load StockItemTestResult table
     */

    function formatDate(row) {
        // Function for formatting date field
        var html = row.date;

        if (row.user_detail) {
            html += `<span class='badge'>${row.user_detail.username}</span>`;
        }

        if (row.attachment) {
            html += `<a href='${row.attachment}'><span class='fas fa-file-alt label-right'></span></a>`;
        }

        return html;
    }

    function makeButtons(row, grouped) {
        var html = `<div class='btn-group float-right' role='group'>`;

        html += makeIconButton('fa-plus icon-green', 'button-test-add', row.test_name, '{% trans "Add test result" %}');

        if (!grouped && row.result != null) {
            var pk = row.pk;
            html += makeIconButton('fa-edit icon-blue', 'button-test-edit', pk, '{% trans "Edit test result" %}');
            html += makeIconButton('fa-trash-alt icon-red', 'button-test-delete', pk, '{% trans "Delete test result" %}');
        }
        
        html += "</div>";

        return html;
    }

    // First, load all the test templates
    table.inventreeTable({
        url: "{% url 'api-part-test-template-list' %}",
        method: 'get',
        name: 'testresult',
        formatNoMatches: function() {
            return "{% trans 'No test results found' %}";
        },
        queryParams: {
            part: options.part,
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
                title: "{% trans "Test Name" %}",
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
            },
            {
                field: 'notes',
                title: '{% trans "Notes" %}',
            },
            {
                field: 'date',
                title: '{% trans "Test Date" %}',
                formatter: function(value, row) {
                    return formatDate(row);
                }
            },
            {
                field: 'buttons',
                formatter: function(value, row) {
                    return makeButtons(row, false);
                }
            },
        ],
        groupBy: true,
        groupByField: 'test_name',
        groupByFormatter: function(field, id, data) {

            // Extract the "latest" row (data are returned in date order from the server)
            var latest = data[data.length-1];

            switch (field) {
            case 'test_name':
                return latest.test_name + ` <i>(${data.length})</i>` + passFailBadge(latest.result);
            case 'value':
                return latest.value;
            case 'notes':
                return latest.notes;
            case 'date':
                return formatDate(latest);
            case 'buttons':
                // Buttons are done differently for grouped rows
                return makeButtons(latest, true);
            default:
                return "---";
            }
        },
        onLoadSuccess: function(tableData) {
            // Once the test template data are loaded, query for results
            inventreeGet(
                "{% url 'api-stock-test-result-list' %}",
                {
                    stock_item: options.stock_item,
                    user_detail: true,
                    attachment_detail: true,
                },
                {
                    success: function(data) {

                        // Iterate through the returned test result data, and group by test
                        data.forEach(function(item) {
                            var match = false;
                            var override = false;

                            var key = item.key;

                            // Try to associate this result with a test row
                            tableData.forEach(function(row, index) {
                                
                                
                                // The result matches the test template row
                                if (key == row.key) {
                                    
                                    // Force the names to be the same!
                                    item.test_name = row.test_name;
                                    item.required = row.required;

                                    if (row.result == null) {
                                        // The original row has not recorded a result - override!
                                        tableData[index] = item;
                                        override = true;
                                    }

                                    match = true;
                                }
                            });

                            // No match could be found (this is a new test!)
                            if (!match) {

                                item.test_name = item.test;
                            }

                            if (!override) {
                                tableData.push(item);
                            }
                        });

                        // Finally, push the data back into the table!
                        table.bootstrapTable("load", tableData);
                    }
                },
            );
        }
    });
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

    options.params['part_detail'] = true;
    options.params['location_detail'] = true;

    var params = options.params || {};

    var filterListElement = options.filterList || "#filter-list-stock";

    var filters = {};

    var filterKey = options.filterKey || options.name || "stock";
     
    if (!options.disableFilters) {
        filters = loadTableFilters(filterKey);
    }

    var original = {};

    for (var key in params) {
        original[key] = params[key];
    }

    setupFilterList(filterKey, table, filterListElement);

    // Override the default values, or add new ones
    for (var key in params) {
        filters[key] = params[key];
    }

    function locationDetail(row) {
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
            url = `/stock/item/${row.belongs_to}/installed/`;
        } else if (row.customer) {
            // StockItem has been assigned to a customer
            text = '{% trans "Shipped to customer" %}';
            url = `/company/${row.customer}/assigned-stock/`;
        } else if (row.sales_order) {
            // StockItem has been assigned to a sales order
            text = '{% trans "Assigned to Sales Order" %}';
            url = `/order/sales-order/${row.sales_order}/`;
        } else if (row.location) {
            text = row.location_detail.pathstring;
            url = `/stock/location/${row.location}/`;
        } else {
            text = '<i>{% trans "No stock location set" %}</i>';
            url = '';
        }

        if (url) {
            return renderLink(text, url);
        } else {
            return text;
        }
    }

    table.inventreeTable({
        method: 'get',
        formatNoMatches: function() {
            return '{% trans "No stock items matching query" %}';
        },
        url: options.url || "{% url 'api-stock-list' %}",
        queryParams: filters,
        customSort: customGroupSorter,
        groupBy: true,
        name: 'stock',
        original: original,
        showColumns: true,
        groupByField: options.groupByField || 'part',
        groupByFormatter: function(field, id, data) {

            var row = data[0];

            if (field == 'part_detail.full_name') {

                var html = imageHoverIcon(row.part_detail.thumbnail);

                html += row.part_detail.full_name;
                html += ` <i>(${data.length} items)</i>`;

                html += makePartIcons(row.part_detail);

                return html;
            }
            else if (field == 'part_detail.IPN') {
                var ipn = row.part_detail.IPN;

                if (ipn) {
                    return ipn;
                } else {
                    return '-';
                }
            }
            else if (field == 'part_detail.description') {
                return row.part_detail.description;
            }
            else if (field == 'quantity') {
                var stock = 0;
                var items = 0;

                data.forEach(function(item) {
                    stock += parseFloat(item.quantity); 
                    items += 1;
                });

                stock = +stock.toFixed(5);

                return stock + " (" + items + " items)";
            } else if (field == 'status') {
                var statii = [];

                data.forEach(function(item) {
                    var status = String(item.status);

                    if (!status || status == '') {
                        status = '-';
                    }

                    if (!statii.includes(status)) {
                        statii.push(status);
                    }
                });

                // Multiple status codes
                if (statii.length > 1) {
                    return "-";
                } else if (statii.length == 1) {
                    return stockStatusDisplay(statii[0]);
                } else {
                    return "-";
                }
            } else if (field == 'batch') {
                var batches = [];

                data.forEach(function(item) {
                    var batch = item.batch;

                    if (!batch || batch == '') {
                        batch = '-';
                    }

                    if (!batches.includes(batch)) {
                        batches.push(batch); 
                    }
                });

                if (batches.length > 1) {
                    return "" + batches.length + " batches";
                } else if (batches.length == 1) {
                    if (batches[0]) {
                        return batches[0];
                    } else {
                        return '-';
                    }
                } else {
                    return '-';
                }
            } else if (field == 'location_detail.pathstring') {
                /* Determine how many locations */
                var locations = [];

                data.forEach(function(item) {

                    var detail = locationDetail(item);

                    if (!locations.includes(detail)) {
                        locations.push(detail);
                    }
                });

                if (locations.length == 1) {
                    // Single location, easy!
                    return locations[0];
                } else if (locations.length > 1) {
                    return "In " + locations.length + " locations";
                } else {
                    return "<i>{% trans "Undefined location" %}</i>";
                }
            } else if (field == 'notes') {
                var notes = [];

                data.forEach(function(item) {
                    var note = item.notes;

                    if (!note || note == '') {
                        note = '-';
                    }

                    if (!notes.includes(note)) {
                        notes.push(note);
                    }
                });

                if (notes.length > 1) {
                    return '...';
                } else if (notes.length == 1) {
                    return notes[0] || '-';
                } else {
                    return '-';
                }
            }
            else {
                return '';
            }
        },
        columns: [
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
            },
            {
                field: 'part_detail.full_name',
                title: '{% trans "Part" %}',
                sortable: true,
                switchable: false,
                formatter: function(value, row, index, field) {

                    var url = `/stock/item/${row.pk}/`;
                    var thumb = row.part_detail.thumbnail;
                    var name = row.part_detail.full_name;

                    html = imageHoverIcon(thumb) + renderLink(name, url);
                    
                    html += makePartIcons(row.part_detail);

                    return html;
                }
            },
            {
                field: 'part_detail.IPN',
                title: 'IPN',
                sortable: true,
                formatter: function(value, row, index, field) {
                    return row.part_detail.IPN;
                },
            },
            {
                field: 'part_detail.description',
                title: '{% trans "Description" %}',
                sortable: true,
                formatter: function(value, row, index, field) {
                    return row.part_detail.description;
                }
            },
            {
                field: 'quantity',
                title: '{% trans "Stock" %}',
                sortable: true,
                formatter: function(value, row, index, field) {

                    var val = parseFloat(value);

                    // If there is a single unit with a serial number, use the serial number
                    if (row.serial && row.quantity == 1) {
                        val = '# ' + row.serial;
                    } else {
                        val = +val.toFixed(5);
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
                    }

                    if (row.expired) {
                        html += makeIconBadge('fa-calendar-times icon-red', '{% trans "Stock item has expired" %}');
                    } else if (row.stale) {
                        html += makeIconBadge('fa-stopwatch', '{% trans "Stock item will expire soon" %}');
                    }

                    if (row.allocated) {
                        html += makeIconBadge('fa-bookmark', '{% trans "Stock item has been allocated" %}');
                    }

                    if (row.belongs_to) {
                        html += makeIconBadge('fa-box', '{% trans "Stock item has been installed in another item" %}');
                    }

                    // Special stock status codes

                    // REJECTED
                    if (row.status == {{ StockStatus.REJECTED }}) {
                        console.log("REJECTED - {{ StockStatus.REJECTED }}");
                        html += makeIconBadge('fa-times-circle icon-red', '{% trans "Stock item has been rejected" %}');
                    }
                    // LOST
                    else if (row.status == {{ StockStatus.LOST }}) {
                        html += makeIconBadge('fa-question-circle','{% trans "Stock item is lost" %}');
                    }
                    else if (row.status == {{ StockStatus.DESTROYED }}) {
                        html += makeIconBadge('fa-skull-crossbones', '{% trans "Stock item is destroyed" %}');
                    }

                    if (row.quantity <= 0) {
                        html += `<span class='label label-right label-danger'>{% trans "Depleted" %}</span>`;
                    }

                    return html;
                }
            },
            {
                field: 'status',
                title: '{% trans "Status" %}',
                sortable: 'true',
                formatter: function(value, row, index, field) {
                    return stockStatusDisplay(value);
                },
            },
            {
                field: 'batch',
                title: '{% trans "Batch" %}',
                sortable: true,
            },
            {
                field: 'location_detail.pathstring',
                title: '{% trans "Location" %}',
                sortable: true,
                formatter: function(value, row, index, field) {
                    return locationDetail(row);
                }
            },
            {% settings_value "STOCK_ENABLE_EXPIRY" as expiry %}
            {% if expiry %}
            {
                field: 'expiry_date',
                title: '{% trans "Expiry Date" %}',
                sortable: true,
            },
            {% endif %}
            {
                field: 'notes',
                title: '{% trans "Notes" %}',
            }
        ],
    });

    if (options.buttons) {
        linkButtonsToSelection(table, options.buttons);
    }

    function stockAdjustment(action) {
        var items = $("#stock-table").bootstrapTable("getSelections");

        var stock = [];

        items.forEach(function(item) {
            stock.push(item.pk);
        });

        // Buttons for launching secondary modals
        var secondary = [];

        if (action == 'move') {
            secondary.push({
                field: 'destination',
                label: '{% trans "New Location" %}',
                title: '{% trans "Create new location" %}',
                url: "/stock/location/new/",
            });
        }

        launchModalForm("/stock/adjust/",
            {
                data: {
                    action: action,
                    stock: stock,
                },
                success: function() {
                    $("#stock-table").bootstrapTable('refresh');
                },
                secondary: secondary,
            }
        );
    }

    // Automatically link button callbacks
    $('#multi-item-stocktake').click(function() {
        stockAdjustment('count');
    });

    $('#multi-item-remove').click(function() {
        stockAdjustment('take');
    });

    $('#multi-item-add').click(function() {
        stockAdjustment('add');
    });

    $("#multi-item-move").click(function() {
        stockAdjustment('move');
    });

    $("#multi-item-order").click(function() {
        var selections = $("#stock-table").bootstrapTable("getSelections");

        var stock = [];

        selections.forEach(function(item) {
            stock.push(item.pk);
        });

        launchModalForm("/order/purchase-order/order-parts/", {
            data: {
                stock: stock,
            },
        });
    });

    $("#multi-item-delete").click(function() {
        var selections = $("#stock-table").bootstrapTable("getSelections");

        var stock = [];

        selections.forEach(function(item) {
            stock.push(item.pk);
        });

        stockAdjustment('delete');
    });
}

function loadStockTrackingTable(table, options) {

    var cols = [
        {
            field: 'pk',
            visible: false,
        },
        {
            field: 'date',
            title: '{% trans "Date" %}',
            sortable: true,
            formatter: function(value, row, index, field) {
                var m = moment(value);
                if (m.isValid()) {
                    var html = m.format('dddd MMMM Do YYYY'); // + '<br>' + m.format('h:mm a');
                    return html;
                }

                return 'N/A';
            }
        },
    ];

    // If enabled, provide a link to the referenced StockItem
    if (options.partColumn) {
        cols.push({
            field: 'item',
            title: '{% trans "Stock Item" %}',
            sortable: true,
            formatter: function(value, row, index, field) {
                return renderLink(value.part_name, value.url);
            }
        });
    }

    // Stock transaction description
    cols.push({
        field: 'title',
        title: '{% trans "Description" %}',
        sortable: true,
        formatter: function(value, row, index, field) {
            var html = "<b>" + value + "</b>";

            if (row.notes) {
                html += "<br><i>" + row.notes + "</i>";
            }

            if (row.link) {
                html += "<br><a href='" + row.link + "'>" + row.link + "</a>";
            }

            return html;
        }
    });

    cols.push({
        field: 'quantity',
        title: '{% trans "Quantity" %}',
        formatter: function(value, row, index, field) {
            return parseFloat(value);
        },
    });

    cols.push({
        sortable: true,
        field: 'user',
        title: '{% trans "User" %}',
        formatter: function(value, row, index, field) {
            if (value)
            {
                // TODO - Format the user's first and last names
                return row.user_detail.username;
            }
            else
            {
                return "{% trans "No user information" %}";
            }
        }
    });

    cols.push({
        sortable: false,
        formatter: function(value, row, index, field) {
            // Manually created entries can be edited or deleted
            if (!row.system) {
                var bEdit = "<button title='Edit tracking entry' class='btn btn-entry-edit btn-default btn-glyph' type='button' url='/stock/track/" + row.pk + "/edit/'><span class='fas fa-edit'/></button>";
                var bDel = "<button title='Delete tracking entry' class='btn btn-entry-delete btn-default btn-glyph' type='button' url='/stock/track/" + row.pk + "/delete/'><span class='fas fa-trash-alt icon-red'/></button>";

                return "<div class='btn-group' role='group'>" + bEdit + bDel + "</div>";
            } else {
                return "";
            }
        }
    });

    table.inventreeTable({
        method: 'get',
        queryParams: options.params,
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


function createNewStockItem(options) {
    /* Launch a modal form to create a new stock item.
     * 
     * This is really just a helper function which calls launchModalForm,
     * but it does get called a lot, so here we are ...
     */

    // Add in some funky options

    options.callback = [
        {   
            field: 'part',
            action: function(value) {

                // Reload options for supplier part
                reloadFieldOptions(
                    'supplier_part',
                    {
                        url: "{% url 'api-supplier-part-list' %}",
                        params: {
                            part: value,
                            pretty: true,
                        },
                        text: function(item) {
                            return item.pretty_name;
                        }
                    }
                );

                // Request part information from the server
                inventreeGet(
                    `/api/part/${value}/`, {},
                    {
                        success: function(response) {
                            
                            // Disable serial number field if the part is not trackable
                            enableField('serial_numbers', response.trackable);
                            clearField('serial_numbers');

                            // Populate the expiry date
                            if (response.default_expiry <= 0) {
                                // No expiry date
                                clearField('expiry_date');
                            } else {
                                var expiry = moment().add(response.default_expiry, 'days');
                                
                                setFieldValue('expiry_date', expiry.format("YYYY-MM-DD"));
                            }
                        }
                    }
                );
            }
        },
    ];

    options.secondary = [
        {
            field: 'part',
            label: '{% trans "New Part" %}',
            title: '{% trans "Create New Part" %}',
            url: "{% url 'part-create' %}",
        },
        {
            field: 'supplier_part',
            label: '{% trans "New Supplier Part" %}',
            title: '{% trans "Create new Supplier Part" %}',
            url: "{% url 'supplier-part-create' %}"
        },
        {
            field: 'location',
            label: '{% trans "New Location" %}',
            title: '{% trans "Create New Location" %}',
            url: "{% url 'stock-location-create' %}",
        },
    ];

    launchModalForm("{% url 'stock-item-create' %}", options);
}


function loadInstalledInTable(table, options) {
    /*
    * Display a table showing the stock items which are installed in this stock item.
    * This is a multi-level tree table, where the "top level" items are Part objects,
    * and the children of each top-level item are the associated installed stock items.
    * 
    * The process for retrieving data and displaying the table is as follows:
    *
    * A) Get BOM data for the stock item
    *    - It is assumed that the stock item will be for an assembly
    *      (otherwise why are we installing stuff anyway?)
    *    - Request BOM items for stock_item.part (and only for trackable sub items)
    * 
    * B) Add parts to table
    *    - Create rows for each trackable sub-part in the table
    *
    * C) Gather installed stock item data
    *    - Get the list of installed stock items via the API
    *    - If the Part reference is already in the table, add the sub-item as a child
    *    - If this is a stock item for a *new* part, request that part from the API,
    *      and add that part as a new row, then add the stock item as a child of that part
    *
    * D) Enjoy!
    *
    *
    * And the options object contains the following things:
    *
    * - stock_item: The PK of the master stock_item object
    * - part: The PK of the Part reference of the stock_item object
    * - quantity: The quantity of the stock item
    */

    function updateCallbacks() {
        // Setup callback functions when buttons are pressed
        table.find('.button-install').click(function() {
            var pk = $(this).attr('pk');

            launchModalForm(
                `/stock/item/${options.stock_item}/install/`,
                {
                    data: {
                        part: pk,
                    },
                    success: function() {
                        // Refresh entire table!
                        table.bootstrapTable('refresh');
                    }
                }
            );
        });
    }

    table.inventreeTable(
        {
            url: "{% url 'api-bom-list' %}",
            queryParams: {
                part: options.part,
                sub_part_trackable: true,
                sub_part_detail: true,
            },
            showColumns: false,
            name: 'installed-in',
            detailView: true,
            detailViewByClick: true,
            detailFilter: function(index, row) {
                return row.installed_count && row.installed_count > 0;
            },
            detailFormatter: function(index, row, element) {
                var subTableId = `installed-table-${row.sub_part}`;

                var html = `<div class='sub-table'><table class='table table-condensed table-striped' id='${subTableId}'></table></div>`;

                element.html(html);

                var subTable = $(`#${subTableId}`);

                // Display a "sub table" showing all the linked stock items
                subTable.bootstrapTable({
                    data: row.installed_items,
                    showHeader: true,
                    columns: [
                        {
                            field: 'item',
                            title: '{% trans "Stock Item" %}', 
                            formatter: function(value, subrow, index, field) {

                                var pk = subrow.pk;
                                var html = '';

                                if (subrow.serial && subrow.quantity == 1) {
                                    html += `{% trans "Serial" %}: ${subrow.serial}`;
                                } else {
                                    html += `{% trans "Quantity" %}: ${subrow.quantity}`; 
                                }

                                return renderLink(html, `/stock/item/${subrow.pk}/`);
                            },
                        },
                        {
                            field: 'status',
                            title: '{% trans "Status" %}',
                            formatter: function(value, subrow, index, field) {
                                return stockStatusDisplay(value);
                            }
                        },
                        {
                            field: 'batch',
                            title: '{% trans "Batch" %}',
                        },
                        {
                            field: 'actions',
                            title: '',
                            formatter: function(value, subrow, index) {

                                var pk = subrow.pk;
                                var html = '';

                                // Add some buttons yo!
                                html += `<div class='btn-group float-right' role='group'>`;
                                
                                html += makeIconButton('fa-unlink', 'button-uninstall', pk, "{% trans "Uninstall stock item" %}");

                                html += `</div>`;

                                return html;
                            }
                        }
                    ],
                    onPostBody: function() {
                        // Setup button callbacks
                        subTable.find('.button-uninstall').click(function() {
                            var pk = $(this).attr('pk');

                            launchModalForm(
                                "{% url 'stock-item-uninstall' %}",
                                {
                                    data: {
                                        'items[]': [pk],
                                    },
                                    success: function() {
                                        // Refresh entire table!
                                        table.bootstrapTable('refresh');
                                    }
                                }
                            );
                        });
                    }
                });
            },
            columns: [
                {
                    checkbox: true,
                    title: '{% trans 'Select' %}',
                    searchable: false,
                    switchable: false,
                },
                {
                    field: 'pk',
                    title: 'ID',
                    visible: false,
                    switchable: false,
                },
                {
                    field: 'part',
                    title: '{% trans "Part" %}',
                    sortable: true,
                    formatter: function(value, row, index, field) {
        
                        var url = `/part/${row.sub_part}/`;
                        var thumb = row.sub_part_detail.thumbnail;
                        var name = row.sub_part_detail.full_name;
        
                        html = imageHoverIcon(thumb) + renderLink(name, url);

                        if (row.not_in_bom) {
                            html = `<i>${html}</i>`
                        }
                        
                        return html;
                    }
                },
                {
                    field: 'installed',
                    title: '{% trans "Installed" %}',
                    sortable: false,
                    formatter: function(value, row, index, field) {
                        // Construct a progress showing how many items have been installed

                        var installed = row.installed_count || 0;
                        var required = row.quantity || 0;

                        required *= options.quantity;

                        var progress = makeProgressBar(installed, required, {
                            id: row.sub_part.pk,
                        });

                        return progress;
                    }
                },
                {
                    field: 'actions',
                    switchable: false,
                    formatter: function(value, row) {
                        var pk = row.sub_part;

                        var html = `<div class='btn-group float-right' role='group'>`;

                        html += makeIconButton('fa-link', 'button-install', pk, '{% trans "Install item" %}');

                        html += `</div>`;

                        return html;
                    }
                }
            ],
            onLoadSuccess: function() {
                // Grab a list of parts which are actually installed in this stock item

                inventreeGet(
                    "{% url 'api-stock-list' %}",
                    {
                        installed_in: options.stock_item,
                        part_detail: true,
                    },
                    {
                        success: function(stock_items) {
                            
                            var table_data = table.bootstrapTable('getData');

                            stock_items.forEach(function(item) {

                                var match = false;
                                
                                for (var idx = 0; idx < table_data.length; idx++) {

                                    var row = table_data[idx];

                                    // Check each row in the table to see if this stock item matches
                                    table_data.forEach(function(row) {

                                        // Match on "sub_part"
                                        if (row.sub_part == item.part) {
                                            
                                            // First time?
                                            if (row.installed_count == null) {
                                                row.installed_count = 0;
                                                row.installed_items = [];
                                            }
                                            
                                            row.installed_count += item.quantity;
                                            row.installed_items.push(item);
                                            
                                            // Push the row back into the table
                                            table.bootstrapTable('updateRow', idx, row, true);

                                            match = true;
                                        }

                                    });

                                    if (match) {
                                        break;
                                    }
                                }

                                if (!match) {
                                    // The stock item did *not* match any items in the BOM!
                                    // Add a new row to the table...
                                    
                                    // Contruct a new "row" to add to the table
                                    var new_row = {
                                        sub_part: item.part,
                                        sub_part_detail: item.part_detail,
                                        not_in_bom: true,
                                        installed_count: item.quantity,
                                        installed_items: [item],
                                    };

                                    table.bootstrapTable('append', [new_row]);

                                }
                            });

                            // Update button callback links
                            updateCallbacks();
                        }
                    }
                );

                updateCallbacks();
            },
        }
    );
}