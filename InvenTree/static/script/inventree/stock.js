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
        var vMax = item.quantity;
        var vCur = item.quantity;

        if (options.action == 'remove') {
            vCur = 0;
        }
        else if (options.action == 'add') {
            vCur = 0;
            vMax = 0;
        }

        html += '<tr>';

        html += '<td>' + item.part.name + '</td>';
        html += '<td>' + item.location.name + '</td>';
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

    html += "<p class='warning-msg'>Note field must be filled</p>";

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

    $(modal).on('click', '#modal-form-submit', function() {

        var stocktake = [];

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
                            success: function(response) {
                                closeModal(modal);
                                if (options.success) {
                                    options.success();
                                }
                            },
                            error: function(error) {
                                alert(error);
                            },
                            method: 'post'
                        }
                        );
    });
}

function adjustStock(options) {
    if (options.items) {
        updateStock(options.items, options);
    }
    else {
        // Lookup of individual item
        if (options.query.pk) {
            getStockDetail(options.query.pk,
                           {
                               success: function(response) {
                                   updateStock([response], options);
                               }
                           });
        }
        else {
            getStockList(options.query,
                 {
                     success: function(response) {
                         updateStock(response, options);
                     }
                 });
         }
    }
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
                buttonText: "Move"
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

            $(modal).on('click', '#modal-form-submit', function() {
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