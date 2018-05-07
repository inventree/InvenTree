
function moveStockItems(items, options) {

    var modal = '#modal-form';

    if ('modal' in options) {
        modal = options.modal;
    }

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
            openModal(modal);
            modalSetTitle(modal, "Move " + items.length + " stock items");
            modalSetButtonText(modal, "Move");

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

function countStockItems(items, options) {
    var modal = '#modal-form';

    if ('modal' in options) {
        modal = options.modal;
    }

    if (items.length == 0) {
        alert('No stock items selected');
        return;
    }

    var tbl = "<table class='table table-striped table-condensed' id='stocktake-table'></table>";

    openModal(modal);
    modalSetTitle(modal, 'Stocktake ' + items.length + ' items');

    $(modal).find('.modal-form-content').html(tbl);

    $(modal).find('#stocktake-table').bootstrapTable({
        data: items,
        columns: [
            {
                checkbox: true,
            },
            {
                field: 'part.name',
                title: 'Part',
            },
            {
                field: 'location.name',
                title: 'Location',
            },
            {
                field: 'quantity',
                title: 'Quantity',
            }
        ]
    });

    $(modal).on('click', '#modal-form-submit', function() {
        var selections = $(modal).find('#stocktake-table').bootstrapTable('getSelections');

        var stocktake = [];

        console.log('Performing stocktake on ' + selections.length + ' items');

        for (i = 0; i<selections.length; i++) {
            var item = {
                pk: selections[i].pk,
                quantity: selections[i].quantity,
            };

            stocktake.push(item);
        }

        inventreeUpdate("/api/stock/stocktake/",
                        {
                            'items[]': stocktake,
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
                            method: 'post',
                        });
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

    openModal(modal);
    modalSetTitle(modal, 'Delete ' + items.length + ' stock items');
}