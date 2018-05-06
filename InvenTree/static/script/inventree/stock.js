
function moveStock(rows, options) {

    var modal = '#modal-form';

    if ('modal' in options) {
        modal = options.modal;
    }

    if (rows.length == 0) {
        alert('No stock items selected');
        return;
    }

    function doMove(location, parts) {
        inventreeUpdate("/api/stock/move/",
                        {
                            location: location,
                            parts: parts
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
                modalSetTitle(modal, "Move " + rows.length + " stock items");
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

                for (i = 0; i < rows.length; i++) {
                    parts.push(rows[i].pk);

                    html += "<li class='list-group-item'>" + rows[i].quantity + " &times " + rows[i].part.name;

                    if (rows[i].location) {
                        html += " (" + rows[i].location.name + ")";
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