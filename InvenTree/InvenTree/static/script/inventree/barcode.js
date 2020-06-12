
/*
 * Pass barcode data to the server.
 */
function scanBarcode(barcode, options={}) {

    console.log('Sending barcode data:');
    console.log(barcode);

    inventreePut(
        '/api/barcode/',
        {
            'barcode': barcode,
        },
        {
            method: 'POST',
            success: function(response, status) {
                console.log(response);
            },
        }
    );
}


function unlinkBarcode(stockitem) {
    /*
     * Remove barcode association from a device.
     */

    showQuestionDialog(
        "Unlink Barcode",
        "Remove barcode association from this Stock Item",
        {
            accept_text: "Unlink",
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
 * Associate barcode data with a StockItem
 */
function associateBarcode(barcode, stockitem, options={}) {

    console.log('Associating barcode data:');
    console.log('barcode: ' + barcode);

    inventreePut(
        '/api/barcode/assign/',
        {
            'barcode': barcode,
            'stockitem': stockitem,
        },
        {
            method: 'POST',
            success: function(response, status) {
                console.log(response);
            },
        }
    );
}


function makeBarcodeInput(placeholderText='') {
    /*
     * Generate HTML for a barcode input
     */

    var html = `
    <div id='barcode-error-message'></div>
    <form class='js-modal-form' method='post'>
    <div class='form-group'>
        <label class='control-label' for='barcode'>Barcode</label>
        <div class='controls'>
            <div class='input-group'>
                <span class='input-group-addon'>
                    <span class='fas fa-qrcode'></span>
                </span>
                <input id='barcode' class='textinput textInput form-control' type='text' name='barcode' placeholder='${placeholderText}'>
            </div>
            <div id='hint_barcode_data' class='help-block'>Enter barcode data</div>
        </div>
    </div>
    </form>
    `;

    return html;
}


function showBarcodeError(modal, message, style='danger') {

    var html = `<div class='alert alert-block alert-${style}'>`;

    html += message;

    html += "</div>";

    $(modal + ' #barcode-error-message').html(html);
}

function clearBarcodeError(modal, message) {

    $(modal + ' #barcode-error-message').html('');
}


function enableBarcodeInput(modal, enabled=true) {

    var barcode = $(modal + ' #barcode');

    barcode.prop('disabled', !enabled);
    
    modalEnable(modal, enabled);
}

function getBarcodeData(modal) {

    modal = modal || '#modal-form';

    var el = $(modal + ' #barcode');

    var barcode = el.val();

    el.val('');
    el.focus();

    return barcode;
}


function barcodeDialog(title, options={}) {
    /*
     * Handle a barcode display dialog.
     */

    var modal = '#modal-form';

    $(modal).on('shown.bs.modal', function() {
        $(modal + ' .modal-form-content').scrollTop(0);
        
        // Ensure the barcode field has focus
        $(modal + ' #barcode').focus();

        var form = $(modal).find('.js-modal-form');

        // Override form submission
        form.submit(function() {

            var barcode = getBarcodeData(modal);

            if (options.submit) {
                options.submit(barcode);
            }

            return false;
        });

        modalSubmit(modal, function() {

            var barcode = getBarcodeData(modal);

            if (options.submit) {
                options.submit(barcode);
            }
        });

    });

    modalSetTitle(modal, title);
    modalShowSubmitButton(modal, true);

    var content = '';

    if (options.headerContent) {
        content += options.headerContent;
    }

    content += makeBarcodeInput();

    if (options.footerContent) {
        content += options.footerContent;
    }

    modalSetContent(modal, content);

    $(modal).modal({
        backdrop: 'static',
        keyboard: false,
    });

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
            headerContent: `<div class='alert alert-info alert-block'>Scan barcode data below</div>`,
            submit: function(barcode) {
                enableBarcodeInput(modal, false);
                inventreePut(
                    '/api/barcode/',
                    {
                        barcode: barcode,
                    },
                    {
                        method: 'POST',
                        success: function(response, status) {

                            console.log(response);

                            enableBarcodeInput(modal, true);

                            if (status == 'success') {
                                
                                if ('success' in response) {
                                    if ('url' in response) {
                                        // Redirect to the URL!
                                        $(modal).modal('hide');
                                        window.location.href = response.url;
                                    }

                                } else if ('error' in response) {
                                    showBarcodeError(modal, response.error, 'warning');
                                } else {
                                    showBarcodeError(modal, "Unknown response from server", 'warning');
                                }
                            } else {
                                showBarcodeError(modal, `Invalid server response.<br>Status code: '${status}'`);
                            }      
                        },
                    },
                );
            }, 
        },
    ); 
}