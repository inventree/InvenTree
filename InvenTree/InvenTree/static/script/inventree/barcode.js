
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