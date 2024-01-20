{% load i18n %}

/* globals
    createNewModal,
    global_settings,
    handleFormError,
    handleFormSuccess,
    Html5Qrcode,
    Html5QrcodeScannerState,
    imageHoverIcon,
    inventreeGet,
    inventreePut,
    makeIcon,
    makeRemoveButton,
    modalEnable,
    modalSetContent,
    modalSetTitle,
    modalSetSubmitText,
    modalShowSubmitButton,
    modalSubmit,
    showApiError,
    showQuestionDialog,
    user_settings,
*/

/* exported
    barcodeCheckInStockItems,
    barcodeCheckInStockLocations,
    barcodeScanDialog,
    linkBarcodeDialog,
    scanItemsIntoLocation,
    unlinkBarcode,
    onBarcodeScanClicked,
*/

var barcodeInputTimer = null;

/*
 * Generate HTML for a barcode scan input
 */
function makeBarcodeInput(placeholderText='', hintText='') {

    placeholderText = placeholderText || '{% jstrans "Scan barcode data here using barcode scanner" %}';

    hintText = hintText || '{% jstrans "Enter barcode data" %}';

    var html = `
    <div id='barcode_scan_video_container' class="mx-auto" style='width: 100%; max-width: 240px; display: none;'>
        <div id="barcode_scan_video"></div>
    </div>
    <div class='form-group'>
        <label class='control-label' for='barcode'>{% jstrans "Barcode" %}</label>
        <div class='controls'>
            <div class='input-group'>
                <span class='input-group-text'>
                    ${makeIcon('fa-qrcode')}
                </span>
                <input id='barcode' class='textinput textInput form-control' type='text' name='barcode' placeholder='${placeholderText}'>
                <button title='{% jstrans "Scan barcode using connected webcam" %}' id='barcode_scan_btn' type='button' class='btn btn-secondary' onclick='onBarcodeScanClicked()' style='display: none;'>
                    ${makeIcon('fa-camera')}
                </button>
            </div>
            <div id='hint_barcode_data' class='help-block'>${hintText}</div>
        </div>
    </div>
    `;

    return html;
}

// Global variables for qrScanner
var qrScanner = null;
var qrScannerCallback = null;


function startQrScanner() {
    $('#barcode_scan_video_container').show();

    const config = {
        fps: 10,
        qrbox: function(viewfinder_width, viewfinder_height) {
            // qrbox should be 80% of shortest viewfinder edge
            var edge_percentage = 0.8;
            var min_edge_size = Math.min(viewfinder_width, viewfinder_height);
            var box_size = Math.floor(min_edge_size * edge_percentage);

            return {
                width: box_size,
                height: box_size
            };
        },
        aspectRatio: 1,
        applyVideoConstraints: {
            focusMode: 'continuous',
        },
    };

    qrScanner.start({facingMode: 'environment'}, config, qrScannerCallback);
}

function stopQrScanner() {
    if (qrScanner != null && qrScanner.getState() != Html5QrcodeScannerState.NOT_STARTED) {
        qrScanner.stop();
    }
    $('#barcode_scan_video_container').hide();
}

function onBarcodeScanClicked(e) {
    if ($('#barcode_scan_video_container').is(':visible') == false) startQrScanner(); else stopQrScanner();
}

function onCameraAvailable(hasCamera, options) {
    if (hasCamera && global_settings.BARCODE_WEBCAM_SUPPORT) {
        // Camera is only accessible if page is served over secure connection
        if (window.isSecureContext == true) {
            qrScanner = new Html5Qrcode('barcode_scan_video', {
                useBarCodeDetectorIfSupported: true,
            });
            qrScannerCallback = (decodedText, decodedResult) => {
                onBarcodeScanCompleted(decodedResult.result, options);
            };
            $('#barcode_scan_btn').show();
        }
    }
}

function onBarcodeScanCompleted(result, options) {
    if (result.text == '') return;
    stopQrScanner();
    postBarcodeData(result.text, options);
}

/*
 * Construct a generic "notes" field for barcode scanning operations
 */
function makeNotesField(options={}) {

    var tooltip = options.tooltip || '{% jstrans "Enter optional notes for stock transfer" %}';
    var placeholder = options.placeholder || '{% jstrans "Enter notes" %}';

    return `
    <div class='form-group'>
        <label class='control-label' for='notes'>{% jstrans "Notes" %}</label>
        <div class='controls'>
            <div class='input-group'>
                <span class='input-group-text'>
                    ${makeIcon('fa-sticky-note')}
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

    var modal = options.modal;

    var url = options.url || '{% url "api-barcode-scan" %}';

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

                    if (options.onError400) {
                        options.onError400(xhr.responseJSON, options);
                    } else {
                        console.error(xhr);
                        data = xhr.responseJSON || {};
                        showBarcodeMessage(modal, data.error || '{% jstrans "Server error" %}');
                    }
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
                            options.onScan(response, options);
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
                            '{% jstrans "Unknown response from server" %}',
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


/*
 * Display an error message when the server indicates an error
 */
function showInvalidResponseError(modal, response, status) {
    showBarcodeMessage(
        modal,
        `{% jstrans "Invalid server response" %}<br>{% jstrans "Status" %}: '${status}'`
    );
}


/*
 * Enable (or disable) the barcode scanning input
 */
function enableBarcodeInput(modal, enabled=true) {

    var barcode = $(modal + ' #barcode');

    barcode.prop('disabled', !enabled);

    modalEnable(modal, enabled);

    barcode.focus();
}


/*
 * Extract scanned data from the barcode input
 */
function getBarcodeData(modal) {

    modal = modal || createNewModal();

    var el = $(modal + ' #barcode');

    var barcode = el.val();

    el.val('');
    el.focus();

    return barcode.trim();
}


/*
 * Handle a barcode display dialog.
 */
function barcodeDialog(title, options={}) {

    var modal = options.modal || createNewModal();

    options.modal = modal;

    function sendBarcode() {
        var barcode = getBarcodeData(modal);

        if (barcode && barcode.length > 0) {
            postBarcodeData(barcode, options);
        }
    }

    $(modal).on('shown.bs.modal', function() {
        $(modal + ' .modal-form-content').scrollTop(0);

        // Check for qr-scanner camera
        Html5Qrcode.getCameras().then( (devices) => {
            var hasCamera = devices && devices.length;
            onCameraAvailable(hasCamera, options);
        });

        var barcode = $(modal + ' #barcode');

        // Handle 'enter' key on barcode
        barcode.keyup(function(event) {
            event.preventDefault();

            if (event.which == 10 || event.which == 13) {
                clearTimeout(barcodeInputTimer);
                sendBarcode();
            } else {
                // Start a timer to automatically send barcode after input is complete
                clearTimeout(barcodeInputTimer);

                barcodeInputTimer = setTimeout(function() {
                    sendBarcode();
                }, global_settings.BARCODE_INPUT_DELAY);
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
        qrScanner = null;
        qrScannerCallback = null;
    });

    modalSetTitle(modal, title);

    if (options.onSubmit) {
        modalShowSubmitButton(modal, true);
    } else {
        modalShowSubmitButton(modal, false);
    }

    var details = options.details || '{% jstrans "Scan barcode data" %}';

    var content = '';

    content += `<div class='alert alert-info alert-block'>${details}</div>`;

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
function barcodeScanDialog(options={}) {

    let modal = options.modal || createNewModal();
    let title = options.title || '{% jstrans "Scan Barcode" %}';

    const matching_models = [
        'build',
        'manufacturerpart',
        'part',
        'purchaseorder',
        'returnorder',
        'salesorder',
        'supplierpart',
        'stockitem',
        'stocklocation'
    ];

    barcodeDialog(
        title,
        {
            onScan: function(response) {

                // Pass the response to the calling function
                if (options.onScan) {
                    options.onScan(response);
                } else {
                    // Find matching model
                    matching_models.forEach(function(model) {
                        if (model in response) {
                            let instance = response[model];
                            let url = instance.web_url || instance.url;
                            if (url) {
                                window.location.href = url;
                                return;
                            }
                        }
                    });

                    // No match
                    showBarcodeMessage(
                        modal,
                        '{% jstrans "No URL in response" %}',
                        'warning'
                    );
                }
            }
        },
    );
}


/*
 * Dialog for linking a particular barcode to a database model instance
 */
function linkBarcodeDialog(data, options={}) {

    var modal = options.modal || createNewModal();
    options.modal = modal;

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

    var html = `<b>{% jstrans "Unlink Barcode" %}</b><br>`;

    html += '{% jstrans "This will remove the link to the associated barcode" %}';

    showQuestionDialog(
        '{% jstrans "Unlink Barcode" %}',
        html,
        {
            accept_text: '{% jstrans "Unlink" %}',
            accept: function() {
                inventreePut(
                    '{% url "api-barcode-unlink" %}',
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
function barcodeCheckInStockItems(location_id, options={}) {

    var modal = options.modal || createNewModal();
    options.modal = modal;

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
                    <th>{% jstrans "Part" %}</th>
                    <th>{% jstrans "Location" %}</th>
                    <th>{% jstrans "Quantity" %}</th>
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
                <td>${makeRemoveButton('button-item-remove', item.pk, '{% jstrans "Remove stock item" %}')}</td>
            </tr>`;
        });

        html += `
            </tbody>
        </table>`;

        table.html(html);

        modalEnable(modal, items.length > 0);

        $(modal + ' #barcode').focus();

        // Callback to remove the scanned item from the table
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

    var table = `<div class='container' id='items-table-div' style='float: left;'></div>`;

    // Extra form fields
    var extra = makeNotesField();

    barcodeDialog(
        '{% jstrans "Scan Stock Items Into Location" %}',
        {
            details: '{% jstrans "Scan stock item barcode to check in to this location" %}',
            headerContent: table,
            preShow: function() {
                modalSetSubmitText(modal, '{% jstrans "Check In" %}');
                modalEnable(modal, false);
                reloadTable();
            },
            onShow: function() {
            },
            extraFields: extra,
            modal: modal,
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
                    showBarcodeMessage(modal, '{% jstrans "No barcode provided" %}', 'warning');
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
                                    showBarcodeMessage(modal, '{% jstrans "Stock Item already scanned" %}', 'warning');
                                } else {

                                    if (stockitem.location == location_id) {
                                        showBarcodeMessage(modal, '{% jstrans "Stock Item already in this location" %}');
                                        return;
                                    }

                                    // Add this stock item to the list
                                    items.push(stockitem);

                                    showBarcodeMessage(modal, '{% jstrans "Added stock item" %}', 'success');

                                    reloadTable();
                                }
                            }
                        }
                    );
                } else {
                    // Barcode does not match a stock item
                    showBarcodeMessage(modal, '{% jstrans "Barcode does not match valid stock item" %}', 'warning');
                }
            },
        }
    );
}


/*
 * Display dialog to scan stock locations into the current location
 */
function barcodeCheckInStockLocations(location_id, options={}) {

    var modal = options.modal || createNewModal();
    options.modal = modal;

    var header = '';

    barcodeDialog(
        '{% jstrans "Scan Stock Container Into Location" %}',
        {
            details: '{% jstrans "Scan stock container barcode to check in to this location" %}',
            headerContent: header,
            preShow: function() {
                modalEnable(modal, false);
            },
            onShow: function() {
                // TODO
            },
            onScan: function(response) {
                if ('stocklocation' in response) {
                    var pk = response.stocklocation.pk;

                    var url = `{% url "api-location-list" %}${pk}/`;

                    // Move the scanned location into *this* location
                    inventreePut(
                        url,
                        {
                            parent: location_id,
                        },
                        {
                            method: 'PATCH',
                            success: function(response) {
                                $(modal).modal('hide');
                                handleFormSuccess(response, options);
                            },
                            error: function(xhr) {
                                $(modal).modal('hide');
                                showApiError(xhr, url);
                            },
                        }
                    );
                } else {
                    // Barcode does not match a valid stock location
                    showBarcodeMessage(modal, '{% jstrans "Barcode does not match valid stock location" %}', 'warning');
                }
            }
        }
    );
}


/*
 * Display dialog to check a single stock item into a stock location
 */
function scanItemsIntoLocation(item_list, options={}) {

    var modal = options.modal || createNewModal();
    options.modal = modal;

    var stock_location = null;

    // Extra form fields
    var extra = makeNotesField();

    // Header content
    var header = `
    <div id='header-div'>
    </div>
    `;

    function updateLocationInfo(location) {
        var div = $(modal + ' #header-div');

        if (location && location.pk) {
            div.html(`
            <div class='alert alert-block alert-info'>
            <b>{% jstrans "Location" %}</b></br>
            ${location.name}<br>
            <i>${location.description}</i>
            </div>
            `);
        } else {
            div.html('');
        }
    }

    barcodeDialog(
        '{% jstrans "Check Into Location" %}',
        {
            headerContent: header,
            extraFields: extra,
            modal: modal,
            preShow: function() {
                modalSetSubmitText(modal, '{% jstrans "Check In" %}');
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

                    inventreeGet(`{% url "api-location-list" %}${pk}/`, {}, {
                        success: function(response) {

                            stock_location = response;

                            updateLocationInfo(stock_location);
                            modalEnable(modal, true);
                        },
                        error: function() {
                            // Barcode does *NOT* correspond to a StockLocation
                            showBarcodeMessage(
                                modal,
                                '{% jstrans "Barcode does not match a valid location" %}',
                                'warning',
                            );
                        }
                    });
                } else {
                    // Barcode does *NOT* correspond to a StockLocation
                    showBarcodeMessage(
                        modal,
                        '{% jstrans "Barcode does not match a valid location" %}',
                        'warning',
                    );
                }
            }
        }
    );
}
