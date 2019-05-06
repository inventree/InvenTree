function inventreeDocReady() {
    /* Run this function when the HTML document is loaded.
     * This will be called for every page that extends "base.html"
     */

    window.addEventListener("dragover",function(e){
        e = e || event;
        e.preventDefault();
      },false);

    window.addEventListener("drop",function(e){
        e = e || event;
        e.preventDefault();
      },false);

    /* Add drag-n-drop functionality to any element
     * marked with the class 'dropzone'
     */
    $('.dropzone').on('dragenter', function() {
        $(this).addClass('dragover');
    });

    $('.dropzone').on('dragleave drop', function() {
        $(this).removeClass('dragover');
    });

    // Callback to launch the 'About' window
    $('#launch-about').click(function() {
        var modal = $('#modal-about');

        modal.modal({
            backdrop: 'static',
            keyboard: 'false',
        });

        modal.modal('show');
    });
}

function isFileTransfer(transfer) {
    /* Determine if a transfer (e.g. drag-and-drop) is a file transfer 
     */

    return transfer.files.length > 0;
}


function isOnlineTransfer(transfer) {
    /* Determine if a drag-and-drop transfer is from another website.
     * e.g. dragged from another browser window
     */

    return transfer.items.length > 0;
}


function getImageUrlFromTransfer(transfer) {
    /* Extract external image URL from a drag-and-dropped image
     */

    console.log(transfer.getData('text/html').match(/src\s*=\s*"(.+?)"/)[1]);
}