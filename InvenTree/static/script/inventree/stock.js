
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

                for (i = 0; i < rows.length; i++) {
                    parts.push(rows[i].pk);
                }

                var form = "<select class='select' id='stock-location'>";

                for (i = 0; i < response.length; i++) {
                    var loc = response[i];

                    form += makeOption(loc.pk, loc.name + ' - <i>' + loc.description + '</i>');
                }

                form += "</select">

                modalSetContent(modal, form);
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