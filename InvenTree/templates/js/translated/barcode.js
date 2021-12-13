{% load i18n %}

/* globals
    imageHoverIcon,
    inventreePut,
    makeIconButton,
    modalEnable,
    modalSetContent,
    modalSetTitle,
    modalSetSubmitText,
    modalShowSubmitButton,
    modalSubmit,
    showAlertOrCache,
    showQuestionDialog,
*/

/* exported
    barcodeCheckIn,
    barcodeScanDialog,
    linkBarcodeDialog,
    scanItemsIntoLocation,
    unlinkBarcode,
    scanOrderIntoBasket,
    scanBarcodeForFulfill
*/

function makeBarcodeInput(placeholderText='', hintText='') {
    /*
     * Generate HTML for a barcode input
     */

    placeholderText = placeholderText || '{% trans "Scan barcode data here using wedge scanner" %}';

    hintText = hintText || '{% trans "Enter barcode data" %}';

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
            <div id='hint_barcode_data' class='help-block'>${hintText}</div>
        </div>
    </div>
    `;

    return html;
}

function makeNotesField(options={}) {

    var tooltip = options.tooltip || '{% trans "Enter optional notes for stock transfer" %}';
    var placeholder = options.placeholder || '{% trans "Enter notes" %}';

    return `
    <div class='form-group'>
        <label class='control-label' for='notes'>{% trans "Notes" %}</label>
        <div class='controls'>
            <div class='input-group'>
                <span class='input-group-addon'>
                    <span class='fas fa-sticky-note'></span>
                </span>
                <input id='notes' class='textinput textInput form-control' type='text' name='notes' placeholder='${placeholder}'>
            </div>
            <div id='hint_notes' class='help_block'>${tooltip}</div>
        </div>
    </div>`;
}

function makeQuantityField(options={}) {
    var tooltip = options.tooltip || '{% trans "Enter quantity for stock transfer" %}';
    var placeholder = options.placeholder || '{% trans "Enter quantity" %}';

    return `
    <div class='form-group'>
        <label class='control-label' for='quantity'>{% trans "Quantity" %}</label>
        <div class='controls'>
            <div class='input-group'>
                <span class='input-group-addon'>
                    <span class='fas fa-th'></i></span>
                </span>
                <input id='quantity' class='textinput textInput form-control' type='number' value='1' name='quantity' placeholder='${placeholder}'>
            </div>
            <div id='quantity' class='help_block'>${tooltip}</div>
        </div>
    </div>`;
}


/*
 * POST data to the server, and handle standard responses.
 */
function postBarcodeData(barcode_data, options={}) {

    var modal = options.modal || '#modal-form';

    var url = options.url || '/api/barcode/';

    var data = options.data || {};

    data.barcode = barcode_data;

    inventreePut(
        url,
        data,
        {
            method: 'POST',
            error: function() {
                enableBarcodeInput(modal, true);
                showBarcodeMessage(modal, '{% trans "Server error" %}');
            },
            success: function(response, status) {
                modalEnable(modal, false);
                enableBarcodeInput(modal, true);

                if (status == 'success') {

                    if ('success' in response) {
                        if (options.onScan) {
                            options.onScan(response);
                        }
                    } else if ('error' in response) {
                        showBarcodeMessage(
                            modal,
                            response.error,
                            'warning'
                        );
                    } else {
                        showBarcodeMessage(
                            modal,
                            '{% trans "Unknown response from server" %}',
                            'warning'
                        );
                    }
                } else {
                    // Invalid response returned from server
                    showInvalidResponseError(modal, response, status);
                }
            }
        }
    );
}


function showBarcodeMessage(modal, message, style='danger') {

    var html = `<div class='alert alert-block alert-${style}'>`;

    html += message;

    html += '</div>';

    $(modal + ' #barcode-error-message').html(html);
}


function showInvalidResponseError(modal, response, status) {
    showBarcodeMessage(modal, `{% trans "Invalid server response" %}<br>{% trans "Status" %}: '${status}'`);
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

            postBarcodeData(barcode, options);
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
        '{% trans "Scan Barcode" %}',
        {
            onScan: function(response) {
                if ('url' in response) {
                    $(modal).modal('hide');

                    // Redirect to the URL!
                    window.location.href = response.url;
                } else {
                    showBarcodeMessage(
                        modal,
                        '{% trans "No URL in response" %}',
                        'warning'
                    );
                }
            } 
        },
    ); 
}


/*
 * Dialog for linking a particular barcode to a stock item.
 */
function linkBarcodeDialog(stockitem) {

    var modal = '#modal-form';

    barcodeDialog(
        '{% trans "Link Barcode to Stock Item" %}',
        {
            url: '/api/barcode/link/',
            data: {
                stockitem: stockitem,
            },
            onScan: function() {

                $(modal).modal('hide');
                location.reload();
            }
        }
    );
}


/*
 * Remove barcode association from a device.
 */
function unlinkBarcode(stockitem) {

    var html = `<b>{% trans "Unlink Barcode" %}</b><br>`;

    html += '{% trans "This will remove the association between this stock item and the barcode" %}';

    showQuestionDialog(
        '{% trans "Unlink Barcode" %}',
        html,
        {
            accept_text: '{% trans "Unlink" %}',
            accept: function() {
                inventreePut(
                    `/api/stock/${stockitem}/`,
                    {
                        // Clear the UID field
                        uid: '',
                    },
                    {
                        method: 'PATCH',
                        success: function() {
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
function barcodeCheckIn(location_id) {

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
    var extra = makeNotesField();

    barcodeDialog(
        '{% trans "Check Stock Items into Location" %}',
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

                var data = {
                    location: location_id
                };

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
                    '{% url "api-stock-transfer" %}',
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
                                showAlertOrCache('alert-success', '{% trans "Error transferring stock" %}', false);
                            }
                        }
                    }
                );
            },
            onScan: function(response) {
                if ('stockitem' in response) {
                    var stockitem = response.stockitem;

                    var duplicate = false;

                    items.forEach(function(item) {
                        if (item.pk == stockitem.pk) {
                            duplicate = true;
                        }
                    });

                    if (duplicate) {
                        showBarcodeMessage(modal, '{% trans "Stock Item already scanned" %}', 'warning');
                    } else {

                        if (stockitem.location == location_id) {
                            showBarcodeMessage(modal, '{% trans "Stock Item already in this location" %}');
                            return;
                        }

                        // Add this stock item to the list
                        items.push(stockitem);

                        showBarcodeMessage(modal, '{% trans "Added stock item" %}', 'success');

                        reloadTable();
                    }

                } else {
                    // Barcode does not match a stock item
                    showBarcodeMessage(modal, '{% trans "Barcode does not match Stock Item" %}', 'warning');
                }
            },
        }
    );
}


/*
 * Display dialog to check a single stock item into a stock location
 */
function scanItemsIntoLocation(item_id_list, options={}) {

    var modal = options.modal || '#modal-form';

    var stock_location = null;

    // Extra form fields
    var extra = makeNotesField();

    // Header contentfor
    var header = `
    <div id='header-div'>
    </div>
    `;

    function updateLocationInfo(location) {
        var div = $(modal + ' #header-div');

        if (location && location.pk) {
            div.html(`
            <div class='alert alert-block alert-info'>
            <b>{% trans "Location" %}</b></br>
            ${location.name}<br>
            <i>${location.description}</i>
            </div>
            `);
        } else {
            div.html('');
        }
    }

    barcodeDialog(
        '{% trans "Check Into Location" %}',
        {
            headerContent: header,
            extraFields: extra,
            preShow: function() {
                modalSetSubmitText(modal, '{% trans "Check In" %}');
                modalEnable(modal, false);
            },
            onShow: function() {
            },
            onSubmit: function() {
                // Called when the 'check-in' button is pressed
                if (!stock_location) {
                    return;
                }

                var items = [];

                item_id_list.forEach(function(pk) {
                    items.push({
                        pk: pk,
                    });
                });

                var data = {
                    location: stock_location.pk,
                    notes: $(modal + ' #notes').val(),
                    items: items,
                };

                // Send API request
                inventreePut(
                    '{% url "api-stock-transfer" %}',
                    data,
                    {
                        method: 'POST',
                        success: function(response, status) {
                            // First hide the modal
                            $(modal).modal('hide');

                            if (status == 'success' && 'success' in response) {
                                showAlertOrCache('alert-success', response.success, true);
                                location.reload();
                            } else {
                                showAlertOrCache('alert-danger', '{% trans "Error transferring stock" %}', false);
                            }
                        }
                    }
                );
            },
            onScan: function(response) {
                updateLocationInfo(null);
                if ('stocklocation' in response) {
                    // Barcode corresponds to a StockLocation
                    stock_location = response.stocklocation;

                    updateLocationInfo(stock_location);
                    modalEnable(modal, true);

                } else {
                    // Barcode does *NOT* correspond to a StockLocation
                    showBarcodeMessage(
                        modal,
                        '{% trans "Barcode does not match a valid location" %}',
                        'warning',
                    );
                }
            }
        }
    );
}


/*
 * Display dialog to check a single stock item into a stock location
 */
function scanOrderIntoBasket(item_id_list, options={}) {

    var modal = options.modal || '#modal-form';

    var basket = null;

    // Extra form fields
    // var extra = makeNotesField();

    // Header contentfor
    var header = `
    <div id='header-div'>
    </div>
    `;

    function updateBasketInfo(basket) {
        var div = $(modal + ' #header-div');
        if (basket && basket.pk) {
            div.html(`
            <div class='alert alert-block alert-info'>
            <b>{% trans "Basket" %}</b></br>
            ${basket.name}<br>
            // <i>${basket.status_text}</i>
            </div>
            `);
        } else {
            div.html('');
        }
    }

    barcodeDialog(
        '{% trans "Check Into Basket" %}',
        {
            headerContent: header,
            // extraFields: extra,
            preShow: function() {
                modalSetSubmitText(modal, '{% trans "Check In" %}');
                modalEnable(modal, false);
            },
            onShow: function() {
            },
            onSubmit: function() {
                // Called when the 'check-in' button is pressed
                if (!basket) {
                    return;
                }

                var items = [];

                item_id_list.forEach(function(pk) {
                    items.push({
                        pk: pk,
                    });
                });

                var data = {
                    order: items[0],
                    basket: basket.pk
                    // notes: $(modal + ' #notes').val(),
                    // orders: orders,
                };

                // Send API request
                inventreePut(
                    "{% url 'api-basket-addorder' %}add_order/",
                    data,
                    {
                        method: 'POST',
                        success: function(response, status) {
                            // First hide the modal
                            $(modal).modal('hide');
                            if (status == 'success' && 'success' in response) {
                                showAlertOrCache('alert-success', response.success, true);
                                location.reload();
                            } else {
                                showAlertOrCache('alert-danger', '{% trans "Error adding order to basket" %}', false);
                            }
                        }
                    }
                );
            },
            onScan: function(response) {
                updateBasketInfo(null);
                if ('orderbasket' in response) {
                    // Barcode corresponds to a StockLocation
                    basket = response.orderbasket;

                    updateBasketInfo(basket);
                    modalEnable(modal, true);

                } else {
                    // Barcode does *NOT* correspond to a StockLocation
                    showBarcodeMessage(
                        modal,
                        '{% trans "Barcode does not match a valid basket" %}',
                        'warning',
                    );
                }
            }
        }
    );
}

function scanBarcodeForAllocate() {
    //Something

}


function scanBarcodeForFulfill(options={}) {

    var modal = options.modal || '#modal-form';

    var stock_item = null;

    // Extra form fields`
    var extra = makeQuantityField();

    // Header contentfor
    var header = `
    <div id='header-div'>
    </div>
    `;

    function checkItemInAllocations() {
        
    }

    function updateInfo(stock_item) {
        var div = $(modal + ' #header-div');

        if (stock_item && stock_item.pk) {
            div.html(`
            <div class='alert alert-block alert-info'>
            <b>{% trans "Stock item" %}</b></br>
            ${stock_item.part_detail.name}<br>
            </div>
            `);
        } else {
            div.html('');
        }
    }

    barcodeDialog(
        '{% trans "Fulfill stock item" %}',
        {
            headerContent: header,
            extraFields: extra,
            preShow: function() {
                modalSetSubmitText(modal, '{% trans "FulFill" %}');
                modalEnable(modal, false);
            },
            onShow: function() {
            },
            onSubmit: function() {
                // Called when the 'check-in' button is pressed
                
                quantity = $('#quantity').val() || 0
                if (!stock_item) {
                    return;
                }
                // Send API request
                inventreePut(
                    `/api/order/so-allocation/fulfill/${stock_item.pk}/${quantity}`,
                    {
                        success: function(response, status) {
                            // First hide the modal
                            $(modal).modal('hide');

                            if (status == 'success' && 'success' in response) {
                                showAlertOrCache('alert-success', response.success, true);
                                location.reload();
                            } else {
                                showAlertOrCache('alert-danger', '{% trans "Error transferring stock" %}', false);
                            }
                        }
                    },
                    {method: 'DELETE'},
                );
            },
            onScan: function(response) {
                updateInfo(null);
                if ('stockitem' in response) {
                    // Barcode corresponds to a StockLocation
                    stock_item = response.stockitem;
                    updateInfo(stock_item);
                    modalEnable(modal, true);

                } else {
                    // Barcode does *NOT* correspond to a StockLocation
                    showBarcodeMessage(
                        modal,
                        '{% trans "Barcode does not match a valid allocated stock item" %}',
                        'warning',
                    );
                }
            }
        }
    );
}
