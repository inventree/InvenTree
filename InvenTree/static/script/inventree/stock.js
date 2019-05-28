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
    html += '<th>' + options.action + '</th>';

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

        html += '<td>' + item.part.full_name + '</td>';

        if (item.location) {
            html += '<td>' + item.location.name + '</td>';
        } else {
            html += '<td><i>No location set</i></td>';
        }

        html += '<td>' + item.quantity + '</td>';

        html += "<td><input class='form-control' ";
        html += "value='" + vCur + "' ";
        html += "min='" + vMin + "' ";

        if (vMax > 0) {
            html += "max='" + vMax + "' ";
        }

        html += "type='number' id='q-update-" + item.pk + "'/></td>";

        html += '</tr>';
    }

    html += '</tbody></table>';

    html += "<hr><input type='text' id='stocktake-notes' placeholder='Notes'/>";
    html += "<p class='help-inline' id='note-warning'><strong>Note field must be filled</strong></p>";

    html += `
        <hr>
        <div class='control-group'>
            <label class='checkbox'>
                <input type='checkbox' id='stocktake-confirm' placeholder='Confirm'/>
                Confirm Stocktake
            </label>
            <p class='help-inline' id='confirm-warning'><strong>Confirm stock count</strong></p>
        </div>`;


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
    $(modal).find('#confirm-warning').hide();

    modalEnable(modal, true);

    modalSubmit(modal, function() {

        var stocktake = [];
        var notes = $(modal).find('#stocktake-notes').val();
        var confirm = $(modal).find('#stocktake-confirm').is(':checked');

        var valid = true;

        if (!notes) {
            $(modal).find('#note-warning').show();
            valid = false;
        }

        if (!confirm) {
            $(modal).find('#confirm-warning').show();
            valid = false;
        }

        if (!valid) {
            return false;
        }

        // Form stocktake data
        for (idx = 0; idx < items.length; idx++) {
            var item = items[idx];

            var q = $(modal).find("#q-update-" + item.pk).val();

            stocktake.push({
                pk: item.pk,
                quantity: q
            });
        };

        if (!valid) {
            alert('Invalid data');
            return false;
        }

        inventreePut("/api/stock/stocktake/",
                        {
                            'action': options.action,
                            'items[]': stocktake,
                            'notes': $(modal).find('#stocktake-notes').val()
                        },
                        {
                            method: 'post',
                        }).then(function(response) {
                            closeModal(modal);
                            afterForm(response, options);
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

    function doMove(location, parts, notes) {
        inventreePut("/api/stock/move/",
            {
                location: location,
                'stock': parts,
                'notes': notes,
            },
            {
                method: 'post',
            }).then(function(response) {
                closeModal(modal);
                afterForm(response, options);
            }).fail(function(xhr, status, error) {
                alert(error);
            });
    }
        

    getStockLocations({},
    {
        success: function(response) {

            // Extact part row info
            var parts = [];

            var html = "Select new location:<br>\n";

            html += "<select class='select' id='stock-location'>";

            for (i = 0; i < response.length; i++) {
                var loc = response[i];

                html += makeOption(loc.pk, loc.name + ' - <i>' + loc.description + '</i>');
            }

            html += "</select><br>";

            html += "<hr><input type='text' id='notes' placeholder='Notes'/>";

            html += "<p class='warning-msg' id='note-warning'><i>Note field must be filled</i></p>";

            html += "<hr>The following stock items will be moved:<hr>";

            html += `
                <table class='table table-striped table-condensed'>
                <tr>
                    <th>Part</th>
                    <th>Location</th>
                    <th>Available</th>
                    <th>Moving</th>
                </tr>
                `;

            for (i = 0; i < items.length; i++) {
                
                parts.push({
                    pk: items[i].pk,
                    quantity: items[i].quantity,
                });

                var item = items[i];

                html += "<tr>";

                html += "<td>" + item.part.full_name + "</td>";
                html += "<td>" + item.location.pathstring + "</td>";
                html += "<td>" + item.quantity + "</td>";

                html += "<td>";
                html += "<input class='form-control' min='0' max='" + item.quantity + "'";
                html += " value='" + item.quantity + "'";
                html += "type='number' id='q-move-" + item.pk + "'/></td>";

                html += "</tr>";
            }

            html += "</table>";

            openModal({
                modal: modal,
                title: "Move " + items.length + " stock items",
                submit_text: "Move",
                content: html
            });

            //modalSetContent(modal, html);
            attachSelect(modal);

            modalEnable(modal, true);

            $(modal).find('#note-warning').hide();

            modalSubmit(modal, function() {
                var locId = $(modal).find("#stock-location").val();

                var notes = $(modal).find('#notes').val();

                if (!notes) {
                    $(modal).find('#note-warning').show();
                    return false;
                }

                // Update the quantity for each item
                for (var ii = 0; ii < parts.length; ii++) {
                    var pk = parts[ii].pk;

                    var q = $(modal).find('#q-move-' + pk).val();

                    parts[ii].quantity = q;
                }

                doMove(locId, parts, notes);
            });
        },
        error: function(error) {
            alert('Error getting stock locations:\n' + error.error);
        }
    });
}

function loadStockTable(table, options) {

    var params = options.params || {};

    // Aggregate stock items 
    //params.aggregate = true;

    table.bootstrapTable({
        sortable: true,
        search: true,
        method: 'get',
        pagination: true,
        pageSize: 25,
        rememberOrder: true,
        groupBy: true,
        groupByField: 'part_name',
        groupByFields: ['part_name', 'test'],
        groupByFormatter: function(field, id, data) {

            if (field == 'Part') {
                return imageHoverIcon(data[0].part_detail.image_url) + 
                    data[0].part_detail.full_name + 
                    ' <i>(' + data.length + ' items)</i>';
            }
            else if (field == 'Description') {
                return data[0].part_detail.description;
            }
            else if (field == 'Stock') {
                var stock = 0;

                data.forEach(function(item) {
                    stock += item.quantity; 
                });

                return stock;
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
                field: 'part_detail',
                title: 'Part',
                sortable: true,
                formatter: function(value, row, index, field) {
                    return imageHoverIcon(value.image_url) + renderLink(value.full_name, value.url + 'stock/');
                }
            },
            {
                field: 'part_detail.description',
                title: 'Description',
                sortable: true,
            },
            {
                field: 'location_detail',
                title: 'Location',
                sortable: true,
                formatter: function(value, row, index, field) {
                    if (value) {
                        return renderLink(value.pathstring, value.url);
                    }
                    else {
                        return '<i>No stock location set</i>';
                    }
                }
            },
            {
                field: 'quantity',
                title: 'Stock',
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
        queryParams: params,
    });

    if (options.buttons) {
        linkButtonsToSelection(table, options.buttons);
    }

    // Automatically link button callbacks
    $('#multi-item-stocktake').click(function() {
        updateStockItems({
            action: 'stocktake',
        });
        return false;
    });

    $('#multi-item-remove').click(function() {
        updateStockItems({
            action: 'remove',
        });
        return false;
    });

    $('#multi-item-add').click(function() {
        updateStockItems({
            action: 'add',
        });
        return false;
    });

    $("#multi-item-move").click(function() {

        var items = $("#stock-table").bootstrapTable('getSelections');

        moveStockItems(items,
                       {
                           success: function() {
                               $("#stock-table").bootstrapTable('refresh');
                           }
                       });

        return false;
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
        pagination: true,
        pageSize: 50,
        url: options.url,
    });

    if (options.buttons) {
        linkButtonsToSelection(table, options.buttons);
    }
}