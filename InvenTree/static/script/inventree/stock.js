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


/* Present user with a dialog to update multiple stock items
 * Possible actions:
 * - Stocktake
 * - Take stock
 * - Add stock
 */
function updateStock(items, options={}) {

    if (!options.action) {
        alert('No action supplied to stock update');
        return false;
    }

    var modal = options.modal || '#modal-form';

    if (items.length == 0) {
        alert('No items selected');
        return;
    }

    var html = '';

    html += "<table class='table table-striped table-condensed' id='stocktake-table'>\n";

    html += '<thead><tr>';
    html += '<th>Item</th>';
    html += '<th>Location</th>';
    html += '<th>Quantity</th>';

    html += '</thead><tbody>';

    for (idx=0; idx<items.length; idx++) {
        var item = items[idx];

        var vMin = 0;
        var vMax = 0;
        var vCur = item.quantity;

        if (options.action == 'remove') {
            vCur = 0;
            vMax = item.quantity;
        }
        else if (options.action == 'add') {
            vCur = 0;
            vMax = 0;
        }

        html += '<tr>';

        html += '<td>' + item.part.name + '</td>';

        if (item.location) {
            html += '<td>' + item.location.name + '</td>';
        } else {
            html += '<td><i>No location set</i></td>';
        }
        html += "<td><input class='form-control' ";
        html += "value='" + vCur + "' ";
        html += "min='" + vMin + "' ";

        if (vMax > 0) {
            html += "max='" + vMax + "' ";
        }

        html += "type='number' id='q-" + item.pk + "'/></td>";

        html += '</tr>';
    }

    html += '</tbody></table>';

    html += "<hr><input type='text' id='stocktake-notes' placeholder='Notes'/>";

    html += "<p class='warning-msg' id='note-warning'><i>Note field must be filled</i></p>";

    var title = '';

    if (options.action == 'stocktake') {
        title = 'Stocktake';
    }
    else if (options.action == 'remove') {
        title = 'Remove stock items';
    }
    else if (options.action == 'add') {
        title = 'Add stock items';
    }

    openModal({
        modal: modal,
        title: title,
        content: html
    });

    $(modal).find('#note-warning').hide();

    modalSubmit(modal, function() {

        var stocktake = [];
        var notes = $(modal).find('#stocktake-notes').val();

        if (!notes) {
            $(modal).find('#note-warning').show();
            return false;
        }

        var valid = true;

        // Form stocktake data
        for (idx = 0; idx < items.length; idx++) {
            var item = items[idx];

            var q = $(modal).find("#q-" + item.pk).val();

            stocktake.push({
                pk: item.pk,
                quantity: q
            });
        };

        if (!valid) {
            alert('Invalid data');
            return false;
        }

        inventreeUpdate("/api/stock/stocktake/",
                        {
                            'action': options.action,
                            'items[]': stocktake,
                            'notes': $(modal).find('#stocktake-notes').val()
                        },
                        {
                            method: 'post',
                        }).then(function(response) {
                            closeModal(modal);
                            if (options.success) {
                                options.success();
                            }
                        }).fail(function(xhr, status, error) {
                            alert(error);
                        });
    });
}


function selectStockItems(options) {
    /* Return list of selections from stock table
     * If options.table not provided, assumed to be '#stock-table'
     */

    var table_name = options.table || '#stock-table';

    // Return list of selected items from the bootstrap table
    return $(table_name).bootstrapTable('getSelections');
}


function adjustStock(options) {
    if (options.items) {
        updateStock(options.items, options);
    }
    else {
        // Lookup of individual item
        if (options.query.pk) {
            getStockDetail(options.query.pk).then(function(response) {
                updateStock([response], options);
            });
        }
        else {
            getStockList(options.query).then(function(response) {
                updateStock(response, options);
            });
         }
    }
}

 
function updateStockItems(options) {
    /* Update one or more stock items selected from a stock-table
     * Options available:
     * 'action' - Action to perform - 'add' / 'remove' / 'stocktake'
     * 'table' - ID of the stock table (default = '#stock-table'
     */

    var table = options.table || '#stock-table';

    var items = selectStockItems({
        table: table,
    });

    // Pass items through
    options.items = items;
    options.table = table;

    // On success, reload the table
    options.success = function() {
        $(table).bootstrapTable('refresh');
    };

    adjustStock(options);
}

function moveStockItems(items, options) {

    var modal = options.modal || '#modal-form';

    if (items.length == 0) {
        alert('No stock items selected');
        return;
    }

    function doMove(location, parts) {
        inventreeUpdate("/api/stock/move/",
                        {
                            location: location,
                            'parts[]': parts
                        },
                        {
                            success: function(response) {
                                closeModal(modal);
                                if (options.success) {
                                    options.success();
                                }
                            },
                            error: function(error) {
                                alert('error!:\n' + error);
                            },
                            method: 'post'
                        });
    }

    getStockLocations({},
    {
        success: function(response) {
            openModal({
                modal: modal,
                title: "Move " + items.length + " stock items",
                submit_text: "Move"
            });

            // Extact part row info
            var parts = [];

            var html = "Select new location:<br>\n";

            html += "<select class='select' id='stock-location'>";

            for (i = 0; i < response.length; i++) {
                var loc = response[i];

                html += makeOption(loc.pk, loc.name + ' - <i>' + loc.description + '</i>');
            }

            html += "</select><br><hr>";

            html += "The following stock items will be moved:<br><ul class='list-group'>\n";

            for (i = 0; i < items.length; i++) {
                parts.push(items[i].pk);

                html += "<li class='list-group-item'>" + items[i].quantity + " &times " + items[i].part.name;

                if (items[i].location) {
                    html += " (" + items[i].location.name + ")";
                }

                html += "</li>\n";
            }

            html += "</ul>\n";

            modalSetContent(modal, html);
            attachSelect(modal);

            modalSubmit(modal, function() {
                var locId = $(modal).find("#stock-location").val();

                doMove(locId, parts);
            });
        },
        error: function(error) {
            alert('Error getting stock locations:\n' + error.error);
        }
    });
}

function deleteStockItems(items, options) {

    var modal = '#modal-delete';

    if ('modal' in options) {
        modal = options.modal;
    }

    if (items.length == 0) {
        alert('No stock items selected');
        return;
    }

    function doDelete(parts) {
        //TODO
    }

    openModal({
        modal: modal,
        title: 'Delete ' + items.length + ' stock items'
    });
}




function loadStockTable(table, options) {

    table.bootstrapTable({
        sortable: true,
        search: true,
        method: 'get',
        pagination: true,
        rememberOrder: true,
        queryParams: options.params,
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
                field: 'part.name',
                title: 'Part',
                sortable: true,
                formatter: function(value, row, index, field) {
                    return renderLink(value, row.part.url);
                }
            },
            {
                field: 'location',
                title: 'Location',
                sortable: true,
                formatter: function(value, row, index, field) {
                    if (row.location) {
                        return renderLink(row.location.pathstring, row.location.url);
                    }
                    else {
                        return '';
                    }
                }
            },
            {
                field: 'quantity',
                title: 'Quantity',
                sortable: true,
                formatter: function(value, row, index, field) {
                    var text = renderLink(value, row.url);
                    text = text + "<span class='badge'>" + row.status_text + "</span>";
                    return text;
                }
            },
            {
                field: 'notes',
                title: 'Notes',
            }
        ],
        url: options.url,
    });

    if (options.buttons) {
        linkButtonsToSelection(table, options.buttons);
    }
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
                    var html = m.format('dddd MMMM Do YYYY') + '<br>' + m.format('h:mm a');
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

            return html;
        }
    });

    cols.push({
        field: 'quantity',
        title: 'Quantity',
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

    table.bootstrapTable({
        sortable: true,
        search: true,
        method: 'get',
        rememberOrder: true,
        queryParams: options.params,
        columns: cols,
        url: options.url,
    });

    if (options.buttons) {
        linkButtonsToSelection(table, options.buttons);
    }
}