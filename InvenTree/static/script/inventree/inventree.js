function inventreeDocReady() {
    /* Run this function when the HTML document is loaded.
     * This will be called for every page that extends "base.html"
     */

    /* Add drag-n-drop functionality to any element
     * marked with the class 'dropzone'
     */
    $('.dropzone').on('dragenter', function() {
        $(this).addClass('dragover');
    });

    $('.dropzone').on('dragleave', function() {
        $(this).removeClass('dragover');
    });
}