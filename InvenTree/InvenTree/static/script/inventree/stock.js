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