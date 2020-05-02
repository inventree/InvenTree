{% load i18n %}

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
            return '{% trans "No stock items matching query" %}';
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
                title: '{% trans "Select" %}',
                searchable: false,
            },
            {
                field: 'pk',
                title: 'ID',
                visible: false,
            },
            {
                field: 'part_name',
                title: '{% trans "Part" %}',
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

                    html = imageHoverIcon(thumb) + renderLink(name, url);
                    
                    return html;
                }
            },
            {
                field: 'part_description',
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
                    
                    if (row.allocated) {
                        html += `<span class='fas fa-bookmark label-right' title='{% trans "StockItem has been allocated" %}'></span>`;
                    }

                    // 70 = "LOST"
                    if (row.status == 70) {
                        html += `<span class='fas fa-question-circle label-right' title='{% trans "StockItem is lost" %}'></span>`;
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
                    if (value) {
                        return renderLink(value, '/stock/location/' + row.location + '/');
                    }
                    else {
                        return '<i>{% trans "No stock location set" %}</i>';
                    }
                }
            },
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
