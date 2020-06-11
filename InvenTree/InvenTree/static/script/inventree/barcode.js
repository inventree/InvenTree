
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