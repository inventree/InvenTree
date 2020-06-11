
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
    <form class='js-modal-form' method='post'>
    <div class='form-group'>
        <label class='control-label' for='barcode'>Barcode</label>
        <div class='controls'>
            <input id='barcode' class='textinput textInput form-control' type='text' name='barcode' placeholder='${placeholderText}'>
            <div id='hint_barcode_data' class='help-block'>Enter barcode data</div>
        </div>
    </div>
    </form>
    `;

    return html;
}


function getBarcodeData(modal) {

    return $(modal + ' #barcode').val();
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
                modalEnable(modal, false);
                options.submit(barcode);
            }

            return false;
        });

        modalSubmit(modal, function() {

            var barcode = getBarcodeData(modal);

            if (options.submit) {
                modalEnable(modal, false);
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
            submit: function(barcode) {
                inventreePut(
                    '/api/barcode/',
                    {
                        barcode: barcode,
                    },
                    {
                        method: 'POST',
                        success: function(response, status) {
                            console.log(response);
                        },
                    },
                );
            }, 
        },
    ); 
}