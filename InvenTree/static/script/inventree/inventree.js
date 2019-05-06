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