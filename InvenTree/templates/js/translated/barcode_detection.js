{% load i18n %}
{% load inventree_extras %}

/* exported
    enableBarcodeDetection
*/

function enableBarcodeDetection() {
    if ({% local_setting_value_js "BARCODE_DETECTION_ENABLED" %}) {
        onScan.attachTo(document, {
            reactToPaste: {% local_setting_value_js "BARCODE_DETECTION_REACTTOPASTE" %},
            minLength: {% local_setting_value_js "BARCODE_DETECTION_MINLENGTH" %},
            suffixKeyCodes: {% local_setting_value_js "BARCODE_DETECTION_SUFFIX" %},
            prefixKeyCodes: {% local_setting_value_js "BARCODE_DETECTION_PREFIX" %},
            scanButtonKeyCode: {% local_setting_value_js "BARCODE_DETECTION_SCANBUTTONKEYCODE" %},
            onScan: function(barcode, iQty) {
                console.log('Scanned: ' + iQty + 'x ' + barcode);
                processDetectedBarcode(barcode);
            },
            ignoreIfFocusOn: 'input',
            keyCodeMapper: barcodeKeyCodeMapper
        });
    }
}

function barcodeKeyCodeMapper(event) {
    if (key !== undefined && key.length == 1) {
        return key;
    }
    return '';
}

function processDetectedBarcode(barcode) {
    let url = '/api/barcode/';
    let data = {
        barcode: barcode
    };
    inventreePut(
        url,
        data,
        {
            method: 'POST',
            error: function(xhr) {

                switch (xhr.status || 0) {
                case 400:
                    let data = xhr.responseJSON || {};
                    showMessage('{% trans "Barcode read" %}', {
                        style: 'warning',
                        icon: 'fas fa-qrcode icon-orange',
                        details: data.error || '{% trans "Server error" %}',
                    });
                    break;
                default:
                    // Any other error code means something went wrong
                    showApiError(xhr, url);
                }
            },
            success: function(response, status) {
                if (status == 'success') {

                    if ('success' in response) {
                        if (response.url) {
                            window.location.href = response.url;
                        }
                    } else if ('error' in response) {
                        showMessage('{% trans "Barcode read" %}', {
                            style: 'warning',
                            icon: 'fas fa-qrcode icon-orange',
                            details: response.error,
                        });
                    } else {
                        showMessage('{% trans "Barcode read" %}', {
                            style: 'warning',
                            icon: 'fas fa-qrcode icon-orange',
                            details: '{% trans "Unknown response from server" %}',
                        });
                    }
                } else {
                    // Invalid response returned from server
                    showMessage('{% trans "Barcode read" %}', {
                        style: 'warning',
                        icon: 'fas fa-qrcode icon-orange',
                        details: `{% trans "Invalid server response" %}<br>{% trans "Status" %}: '${status}'`,
                    });
                }
            }
        }
    );
}
