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
    showQuestionDialog,
*/

/* exported
    barcodeCheckIn,
    barcodeScanDialog,
    linkBarcodeDialog,
    scanItemsIntoLocation,
    unlinkBarcode,
    onBarcodeScanClicked,
*/

function makeBarcodeInput(placeholderText='', hintText='') {
    /*
     * Generate HTML for a barcode input
     */

    placeholderText = placeholderText || '{% trans "Scan barcode data here using wedge scanner" %}';

    hintText = hintText || '{% trans "Enter barcode data" %}';

    var html = `
    <div id='barcode_scan_video_container' class='text-center' style='height: 240px; display: none;'>
        <video id='barcode_scan_video' disablepictureinpicture playsinline height='240' style='object-fit: fill;'></video>
    </div>
    <div class='form-group'>
        <label class='control-label' for='barcode'>{% trans "Barcode" %}</label>
        <div class='controls'>
            <div class='input-group'>
                <span class='input-group-text'>
                    <span class='fas fa-qrcode'></span>
                </span>
                <input id='barcode' class='textinput textInput form-control' type='text' name='barcode' placeholder='${placeholderText}'>
                <button id='barcode_scan_btn' type='button' class='btn btn-secondary' onclick='onBarcodeScanClicked()' style='display: none;'>
                    <span class='fas fa-camera'></span>
                </button>
            </div>
            <div id='hint_barcode_data' class='help-block'>${hintText}</div>
        </div>
    </div>
    `;

    return html;
}

qrScanner = null;

function startQrScanner() {
    $('#barcode_scan_video_container').show();
    qrScanner.start();
}

function stopQrScanner() {
    if (qrScanner != null) qrScanner.stop();
    $('#barcode_scan_video_container').hide();
}

function onBarcodeScanClicked(e) {
    if ($('#barcode_scan_video_container').is(':visible') == false) startQrScanner(); else stopQrScanner();
}

function onCameraAvailable(hasCamera, options) {
    if (hasCamera && global_settings.BARCODE_WEBCAM_SUPPORT) {
        // Camera is only acccessible if page is served over secure connection
        if ( window.isSecureContext == true ) {
            qrScanner = new QrScanner(document.getElementById('barcode_scan_video'), (result) => {
                onBarcodeScanCompleted(result, options);
            }, {
                highlightScanRegion: true,
                highlightCodeOutline: true,
            });
            $('#barcode_scan_btn').show();
        }
    }
}

function onBarcodeScanCompleted(result, options) {
    if (result.data == '') return;
    stopQrScanner();
    postBarcodeData(result.data, options);
}

function makeNotesField(options={}) {

    var tooltip = options.tooltip || '{% trans "Enter optional notes for stock transfer" %}';
    var placeholder = options.placeholder || '{% trans "Enter notes" %}';

    return `
    <div class='form-group'>
        <label class='control-label' for='notes'>{% trans "Notes" %}</label>
        <div class='controls'>
            <div class='input-group'>
                <span class='input-group-text'>
                    <span class='fas fa-sticky-note'></span>
                </span>
                <input id='notes' class='textinput textInput form-control' type='text' name='notes' placeholder='${placeholder}'>
            </div>
            <div id='hint_notes' class='help_block'>${tooltip}</div>
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
            error: function(xhr) {

                enableBarcodeInput(modal, true);

                switch (xhr.status || 0) {
                case 400:
                    // No match for barcode, most likely
                    console.log(xhr);

                    data = xhr.responseJSON || {};
                    showBarcodeMessage(modal, data.error || '{% trans "Server error" %}');

                    break;
                default:
                    // Any other error code means something went wrong
                    $(modal).modal('hide');

                    showApiError(xhr, url);
                }
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


/*
 * Display a message within the barcode scanning dialog
 */
function showBarcodeMessage(modal, message, style='danger') {

    var html = `<div class='alert alert-block alert-${style}'>`;

    html += message;

    html += '</div>';

    $(modal + ' #barcode-error-message').html(html);
}


function showInvalidResponseError(modal, response, status) {
    showBarcodeMessage(
        modal,
        `{% trans "Invalid server response" %}<br>{% trans "Status" %}: '${status}'`
    );
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

        // Check for qr-scanner camera
        QrScanner.hasCamera().then( (hasCamera) => {
            onCameraAvailable(hasCamera, options);
        });

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

    $(modal).on('hidden.bs.modal', function() {
        stopQrScanner();
        if (qrScanner != null) qrScanner.destroy();
        qrScanner = null;
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
        keyboard: user_settings.FORMS_CLOSE_USING_ESCAPE,
    });

    if (options.preShow) {
        options.preShow();
    }

    $(modal).modal('show');
}

/*
* Perform a barcode scan,
* and (potentially) redirect the browser
*/
function barcodeScanDialog() {

    var modal = '#modal-form';

    barcodeDialog(
        '{% trans "Scan Barcode" %}',
        {
            onScan: function(response) {

                var url = response.url;

                if (url) {
                    $(modal).modal('hide');
                    window.location.href = url;
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
 * Dialog for linking a particular barcode to a database model instsance
 */
function linkBarcodeDialog(data, options={}) {

    var modal = '#modal-form';

    barcodeDialog(
        options.title,
        {
            url: '/api/barcode/link/',
            data: data,
            onScan: function() {

                $(modal).modal('hide');
                location.reload();
            }
        }
    );
}


/*
 * Remove barcode association from a database model instance.
 */
function unlinkBarcode(data, options={}) {

    var html = `<b>{% trans "Unlink Barcode" %}</b><br>`;

    html += '{% trans "This will remove the link to the associated barcode" %}';

    showQuestionDialog(
        '{% trans "Unlink Barcode" %}',
        html,
        {
            accept_text: '{% trans "Unlink" %}',
            accept: function() {
                inventreePut(
                    '/api/barcode/unlink/',
                    data,
                    {
                        method: 'POST',
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

            var location_info = `${item.location}`;

            if (item.location_detail) {
                location_info = `${item.location_detail.name}`;
            }

            html += `
            <tr pk='${item.pk}'>
                <td>${imageHoverIcon(item.part_detail.thumbnail)} ${item.part_detail.name}</td>
                <td>${location_info}</td>
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

                // Prevent submission without any entries
                if (entries.length == 0) {
                    showBarcodeMessage(modal, '{% trans "No barcode provided" %}', 'warning');
                    return;
                }

                inventreePut(
                    '{% url "api-stock-transfer" %}',
                    data,
                    {
                        method: 'POST',
                        success: function(response, status) {
                            // Hide the modal
                            $(modal).modal('hide');

                            if (options.success) {
                                options.success(response);
                            } else {
                                location.reload();
                            }
                        }
                    }
                );
            },
            onScan: function(response) {
                if ('stockitem' in response) {
                    var pk = response.stockitem.pk;

                    inventreeGet(
                        `/api/stock/${pk}/`,
                        {},
                        {
                            success: function(stockitem) {
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
                            }
                        }
                    );
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
function scanItemsIntoLocation(item_list, options={}) {

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

                item_list.forEach(function(item) {
                    items.push({
                        pk: item.pk || item.id,
                        quantity: item.quantity,
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

                            if (options.success) {
                                options.success(response);
                            } else {
                                location.reload();
                            }
                        }
                    }
                );
            },
            onScan: function(response) {
                updateLocationInfo(null);
                if ('stocklocation' in response) {

                    var pk = response.stocklocation.pk;

                    inventreeGet(`/api/stock/location/${pk}/`, {}, {
                        success: function(response) {

                            stock_location = response;

                            updateLocationInfo(stock_location);
                            modalEnable(modal, true);
                        },
                        error: function() {
                            // Barcode does *NOT* correspond to a StockLocation
                            showBarcodeMessage(
                                modal,
                                '{% trans "Barcode does not match a valid location" %}',
                                'warning',
                            );
                        }
                    });
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
