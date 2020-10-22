{% load i18n %}

function makeBarcodeInput(placeholderText='') {
    /*
     * Generate HTML for a barcode input
     */

    placeholderText = placeholderText || '{% trans "Scan barcode data here using wedge scanner" %}';

    var html = `
    <div class='form-group'>
        <label class='control-label' for='barcode'>{% trans "Barcode" %}</label>
        <div class='controls'>
            <div class='input-group'>
                <span class='input-group-addon'>
                    <span class='fas fa-qrcode'></span>
                </span>
                <input id='barcode' class='textinput textInput form-control' type='text' name='barcode' placeholder='${placeholderText}'>
            </div>
            <div id='hint_barcode_data' class='help-block'>{% trans "Enter barcode data" %}</div>
        </div>
    </div>
    `;

    return html;
}


function showBarcodeMessage(modal, message, style='danger') {

    var html = `<div class='alert alert-block alert-${style}'>`;

    html += message;

    html += "</div>";

    $(modal + ' #barcode-error-message').html(html);
}


function showInvalidResponseError(modal, response, status) {
    showBarcodeMessage(modal, `{% trans "Invalid server response" %}<br>{% trans "Status" %}: '${status}'`);
}


function clearBarcodeError(modal, message) {

    $(modal + ' #barcode-error-message').html('');
}


function enableBarcodeInput(modal, enabled=true) {

    var barcode = $(modal + ' #barcode');

    barcode.prop('disabled', !enabled);
    
    modalEnable(modal, enabled);

    barcode.focus();
}

function getBarcodeData(modal) {

    modal = modal || '#modal-form';

    var el = $(modal + ' #barcode');

    var barcode = el.val();

    el.val('');
    el.focus();

    return barcode.trim();
}


function barcodeDialog(title, options={}) {
    /*
     * Handle a barcode display dialog.
     */

    var modal = '#modal-form';

    function sendBarcode() {
        var barcode = getBarcodeData(modal);

        if (barcode && barcode.length > 0) {
            
            if (options.onScan) {
                options.onScan(barcode);
            }
        }
    }

    $(modal).on('shown.bs.modal', function() {
        $(modal + ' .modal-form-content').scrollTop(0);
        
        var barcode = $(modal + ' #barcode');

        // Handle 'enter' key on barcode
        barcode.keyup(function(event) {
            event.preventDefault();

            if (event.which == 10 || event.which == 13) {
                sendBarcode();
            }
        });

        // Ensure the barcode field has focus
        barcode.focus();

        var form = $(modal).find('.js-modal-form');

        // Override form submission
        form.submit(function() {
            return false;
        });

        // Callback for when the "submit" button is pressed on the modal
        modalSubmit(modal, function() {
            if (options.onSubmit) {
                options.onSubmit();
            }
        });

        if (options.onShow) {
            options.onShow();
        }

    });

    modalSetTitle(modal, title);

    if (options.onSubmit) {
        modalShowSubmitButton(modal, true);
    } else {
        modalShowSubmitButton(modal, false);
    }

    var content = '';

    content += `<div class='alert alert-info alert-block'>{% trans "Scan barcode data below" %}</div>`;
    
    content += `<div id='barcode-error-message'></div>`;
    content += `<form class='js-modal-form' method='post'>`;
    
    // Optional content before barcode input
    content += `<div class='container' id='barcode-header'>`;
    content += options.headerContent || '';
    content += `</div>`;

    content += makeBarcodeInput();

    if (options.extraFields) {
        content += options.extraFields;
    }

    content += `</form>`;

    // Optional content after barcode input
    content += `<div class='container' id='barcode-footer'>`;
    content += options.footerContent || '';
    content += '</div>';

    modalSetContent(modal, content);

    $(modal).modal({
        backdrop: 'static',
        keyboard: false,
    });

    if (options.preShow) {
        options.preShow();
    }

    $(modal).modal('show');
}


function barcodeScanDialog() {
    /*
     * Perform a barcode scan,
     * and (potentially) redirect the browser 
     */

    var modal = '#modal-form';
    
    barcodeDialog(
        "Scan Barcode",
        {
            onScan: function(barcode) {
                enableBarcodeInput(modal, false);
                inventreePut(
                    '/api/barcode/',
                    {
                        barcode: barcode,
                    },
                    {
                        method: 'POST',
                        success: function(response, status) {

                            enableBarcodeInput(modal, true);

                            if (status == 'success') {
                                
                                if ('success' in response) {
                                    if ('url' in response) {
                                        // Redirect to the URL!
                                        $(modal).modal('hide');
                                        window.location.href = response.url;
                                    }

                                } else if ('error' in response) {
                                    showBarcodeMessage(modal, response.error, 'warning');
                                } else {
                                    showBarcodeMessage(modal, "{% trans 'Unknown response from server' %}", 'warning');
                                }
                            } else {
                                showInvalidResponseError(modal, response, status);
                            }      
                        },
                    },
                );
            }, 
        },
    ); 
}


/*
 * Dialog for linking a particular barcode to a stock item.
 */
function linkBarcodeDialog(stockitem, options={}) {

    var modal = '#modal-form';

    barcodeDialog(
        "{% trans 'Link Barcode to Stock Item' %}",
        {
            onScan: function(barcode) {
                enableBarcodeInput(modal, false);
                inventreePut(
                    '/api/barcode/link/',
                    {
                        barcode: barcode,
                        stockitem: stockitem,
                    },
                    {
                        method: 'POST',
                        success: function(response, status) {

                            enableBarcodeInput(modal, true);

                            if (status == 'success') {

                                if ('success' in response) {
                                    $(modal).modal('hide');
                                    location.reload();
                                } else if ('error' in response) {
                                    showBarcodeMessage(modal, response.error, 'warning');
                                } else {
                                    showBarcodeMessage(modal, "{% trans 'Unknown response from server' %}", warning);
                                }

                            } else {
                                showInvalidResponseError(modal, response, status);
                            }
                        },
                    },
                );
            }
        }
    );
}


/*
 * Remove barcode association from a device.
 */
function unlinkBarcode(stockitem) {

    var html = `<b>{% trans "Unlink Barcode" %}</b><br>`;

    html += "{% trans 'This will remove the association between this stock item and the barcode' %}";

    showQuestionDialog(
        "{% trans 'Unlink Barcode' %}",
        html,
        {
            accept_text: "{% trans 'Unlink' %}",
            accept: function() {
                inventreePut(
                    `/api/stock/${stockitem}/`,
                    {
                        // Clear the UID field
                        uid: '',
                    },
                    {
                        method: 'PATCH',
                        success: function(response, status) {
                            location.reload();
                        },
                    },
                );
            },
        }
    );
}


/*
 * Display dialog to check multiple stock items in to a stock location.
 */
function barcodeCheckIn(location_id, options={}) {

    var modal = '#modal-form';

    // List of items we are going to checkin
    var items = [];


    function reloadTable() {

        modalEnable(modal, false);

        // Remove click listeners
        $(modal + ' .button-item-remove').unbind('click');

        var table = $(modal + ' #items-table-div');

        var html = `
        <table class='table table-condensed table-striped' id='items-table'>
            <thead>
                <tr>
                    <th>{% trans "Part" %}</th>
                    <th>{% trans "Location" %}</th>
                    <th>{% trans "Quantity" %}</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>`;

        items.forEach(function(item) {
            html += `
            <tr pk='${item.pk}'>
                <td>${imageHoverIcon(item.part_detail.thumbnail)} ${item.part_detail.name}</td>
                <td>${item.location_detail.name}</td>
                <td>${item.quantity}</td>
                <td>${makeIconButton('fa-times-circle icon-red', 'button-item-remove', item.pk, '{% trans "Remove stock item" %}')}</td>
            </tr>`;
        });

        html += `
            </tbody>
        </table>`;

        table.html(html);

        modalEnable(modal, items.length > 0);

        $(modal + ' #barcode').focus();

        $(modal + ' .button-item-remove').unbind('click').on('mouseup', function() {
            var pk = $(this).attr('pk');

            var match = false;

            for (var ii = 0; ii < items.length; ii++) {
                if (pk.toString() == items[ii].pk.toString()) {
                    items.splice(ii, 1);
                    match = true;
                    break;
                }
            }
            
            if (match) {
                reloadTable();
            }

            return false;

        });
    }

    var table = `<div class='container' id='items-table-div' style='width: 80%; float: left;'></div>`;

    // Extra form fields
    var extra = `
    <div class='form-group'>
        <label class='control-label' for='notes'>{% trans "Notes" %}</label>
        <div class='controls'>
            <div class='input-group'>
                <span class='input-group-addon'>
                    <span class='fas fa-sticky-note'></span>
                </span>
                <input id='notes' class='textinput textInput form-control' type='text' name='notes' placeholder='{% trans "Enter notes" %}'>
            </div>
            <div id='hint_notes' class='help_block'>{% trans "Enter optional notes for stock transfer" %}</div>
        </div>
    </div>`;

    barcodeDialog(
        "{% trans "Check Stock Items into Location" %}",
        {
            headerContent: table,
            preShow: function() {
                modalSetSubmitText(modal, '{% trans "Check In" %}');
                modalEnable(modal, false);
                reloadTable();
            },
            onShow: function() {
            },
            extraFields: extra,
            onSubmit: function() {


                // Called when the 'check-in' button is pressed
                
                var data = {location: location_id};
                
                // Extract 'notes' field
                data.notes = $(modal + ' #notes').val();

                var entries = [];

                items.forEach(function(item) {
                    entries.push({
                        pk: item.pk,
                        quantity: item.quantity,
                    });
                });

                data.items = entries;

                inventreePut(
                    '{% url 'api-stock-transfer' %}',
                    data,
                    {
                        method: 'POST',
                        success: function(response, status) {
                            // Hide the modal
                            $(modal).modal('hide');
                            if (status == 'success' && 'success' in response) {

                                showAlertOrCache('alert-success', response.success, true);
                                location.reload();
                            } else {
                                showAlertOrCache('alert-success', 'Error transferring stock', false);
                            }
                        }
                    }
                );
            },
            onScan: function(barcode) {
                enableBarcodeInput(modal, false);
                inventreePut(
                    '/api/barcode/',
                    {
                        barcode: barcode,
                    },
                    {
                        method: 'POST',
                        error: function() {
                            enableBarcodeInput(modal, true);
                            showBarcodeMessage(modal, '{% trans "Server error" %}');
                        },
                        success: function(response, status) {

                            enableBarcodeInput(modal, true);

                            if (status == 'success') {
                                if ('stockitem' in response) {
                                    stockitem = response.stockitem;

                                    var duplicate = false;

                                    items.forEach(function(item) {
                                        if (item.pk == stockitem.pk) {
                                            duplicate = true;
                                        }
                                    });

                                    if (duplicate) {
                                        showBarcodeMessage(modal, "{% trans "Stock Item already scanned" %}", "warning");
                                    } else {

                                        if (stockitem.location == location_id) {
                                            showBarcodeMessage(modal, "{% trans "Stock Item already in this location" %}");
                                            return;
                                        }

                                        // Add this stock item to the list
                                        items.push(stockitem);

                                        showBarcodeMessage(modal, "{% trans "Added stock item" %}", "success");

                                        reloadTable();
                                    }

                                } else {
                                    // Barcode does not match a stock item
                                    showBarcodeMessage(modal, "{% trans "Barcode does not match Stock Item" %}", "warning");
                                }
                            } else {
                                showInvalidResponseError(modal, response, status);
                            }
                        },
                    },
                );
            },
        }
    );
}
