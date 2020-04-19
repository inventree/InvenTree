/* Stock API functions
 * Requires api.js to be loaded first
 */

function getStockList(filters={}, options={}) {
    return inventreeGet('/api/stock/', filters, options);
}

function getStockDetail(pk, options={}) {
    return inventreeGet('/api/stock/' + pk + '/', {}, options)
}

function getStockLocations(filters={}, options={}) {
    return inventreeGet('/api/stock/location/', filters, options)
}


/* Functions for interacting with stock management forms
 */

function removeStockRow(e) {
    // Remove a selected row from a stock modal form

    e = e || window.event;
    var src = e.target || e.srcElement;

    var row = $(src).attr('row');

    $('#' + row).remove();
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

    var params = options.params || {};

    var filterListElement = options.filterList || "#filter-list-stock";

    var filters = {};
    
    if (!options.disableFilters) {
        filters = loadTableFilters("stock");
    }

    var original = {};

    for (var key in params) {
        original[key] = params[key];
    }

    setupFilterList("stock", table, filterListElement);

    // Override the default values, or add new ones
    for (var key in params) {
        filters[key] = params[key];
    }

    table.inventreeTable({
        method: 'get',
        formatNoMatches: function() {
            return 'No stock items matching query';
        },
        url: options.url,
        queryParams: filters,
        customSort: customGroupSorter,
        groupBy: true,
        original: original,
        groupByField: options.groupByField || 'part',
        groupByFormatter: function(field, id, data) {

            var row = data[0];

            if (field == 'part_name') {

                var name = row.part_detail.full_name;

                return imageHoverIcon(row.part_detail.thumbnail) + name + ' <i>(' + data.length + ' items)</i>';
            }
            else if (field == 'part_description') {
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
            } else if (field == 'location__path') {
                /* Determine how many locations */
                var locations = [];

                data.forEach(function(item) {
                    var loc = item.location;

                    if (!locations.includes(loc)) {
                        locations.push(loc); 
                    }
                });

                if (locations.length > 1) {
                    return "In " + locations.length + " locations";
                } else {
                    // A single location!
                    return renderLink(row.location__path, '/stock/location/' + row.location + '/')
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
                title: 'Select',
                searchable: false,
            },
            {
                field: 'pk',
                title: 'ID',
                visible: false,
            },
            {
                field: 'part_name',
                title: 'Part',
                sortable: true,
                formatter: function(value, row, index, field) {

                    var url = '';
                    var thumb = row.part_detail.thumbnail;
                    var name = row.part_detail.full_name;

                    if (row.supplier_part) {
                        url = `/supplier-part/${row.supplier_part}/`;
                    } else {
                        url = `/part/${row.part}/`;
                    }
                    
                    return imageHoverIcon(thumb) + renderLink(name, url);
                }
            },
            {
                field: 'part_description',
                title: 'Description',
                sortable: true,
                formatter: function(value, row, index, field) {
                    return row.part_detail.description;
                }
            },
            {
                field: 'quantity',
                title: 'Stock',
                sortable: true,
                formatter: function(value, row, index, field) {

                    var val = parseFloat(value);

                    // If there is a single unit with a serial number, use the serial number
                    if (row.serial && row.quantity == 1) {
                        val = '# ' + row.serial;
                    } else {
                        val = +val.toFixed(5);
                    }

                    var text = renderLink(val, '/stock/item/' + row.pk + '/');
                    
                    return text;
                }
            },
            {
                field: 'status',
                title: 'Status',
                sortable: 'true',
                formatter: function(value, row, index, field) {
                    return stockStatusDisplay(value);
                },
            },
            {
                field: 'batch',
                title: 'Batch',
                sortable: true,
            },
            {
                field: 'location_detail.pathstring',
                title: 'Location',
                sortable: true,
                formatter: function(value, row, index, field) {
                    if (value) {
                        return renderLink(value, '/stock/location/' + row.location + '/');
                    }
                    else {
                        return '<i>No stock location set</i>';
                    }
                }
            },
            {
                field: 'notes',
                title: 'Notes',
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
                label: 'New Location',
                title: 'Create new location',
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
            title: 'Date',
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
            title: 'Stock Item',
            sortable: true,
            formatter: function(value, row, index, field) {
                return renderLink(value.part_name, value.url);
            }
        });
    }

    // Stock transaction description
    cols.push({
        field: 'title',
        title: 'Description',
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
        title: 'Quantity',
        formatter: function(value, row, index, field) {
            return parseFloat(value);
        },
    });

    cols.push({
        sortable: true,
        field: 'user',
        title: 'User',
        formatter: function(value, row, index, field) {
            if (value)
            {
                // TODO - Format the user's first and last names
                return value.username;
            }
            else
            {
                return "No user information";
            }
        }
    });

    cols.push({
        sortable: false,
        formatter: function(value, row, index, field) {
            // Manually created entries can be edited or deleted
            if (!row.system) {
                var bEdit = "<button title='Edit tracking entry' class='btn btn-entry-edit btn-default btn-glyph' type='button' url='/stock/track/" + row.pk + "/edit/'><span class='glyphicon glyphicon-edit'/></button>";
                var bDel = "<button title='Delete tracking entry' class='btn btn-entry-delete btn-default btn-glyph' type='button' url='/stock/track/" + row.pk + "/delete/'><span class='glyphicon glyphicon-trash'/></button>";

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