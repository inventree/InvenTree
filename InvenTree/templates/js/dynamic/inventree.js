{% load inventree_extras %}

function attachClipboard(selector, containerselector, textElement) {
    // set container
    if (containerselector){
        containerselector = document.getElementById(containerselector);
    } else {
        containerselector = document.body;
    }

    // set text-function
    if (textElement){
        text = function() {
            return document.getElementById(textElement).textContent;
        }
    } else {
        text = function(trigger) {
            var content = trigger.parentElement.parentElement.textContent;
            return content.trim();
        }
    }

    // create Clipboard
    var cis = new ClipboardJS(selector, {
        text: text,
        container: containerselector
    });
}


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
    $('.dropzone').on('dragenter', function(event) {

        // TODO - Only indicate that a drop event will occur if a file is being dragged
        var transfer = event.originalEvent.dataTransfer;

        if (true || isFileTransfer(transfer)) {
            $(this).addClass('dragover');
        }
    });

    $('.dropzone').on('dragleave drop', function(event) {
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

    // Callback to launch the 'Database Stats' window
    $('#launch-stats').click(function() {
        launchModalForm("/stats/", {
            no_post: true,
        });
    });

    // Initialize clipboard-buttons
    attachClipboard('.clip-btn');
    attachClipboard('.clip-btn', 'modal-about');  // modals
    attachClipboard('.clip-btn-version', 'modal-about', 'about-copy-text');  // version-text

    // Add autocomplete to the search-bar
    $("#search-bar" ).autocomplete({
        source: function (request, response) {
            $.ajax({
                url: '/api/part/',
                data: {
                    search: request.term,
                    limit: user_settings.SEARCH_PREVIEW_RESULTS,
                    offset: 0
                },
                success: function (data) {
                    var transformed = $.map(data.results, function (el) {
                        return {
                            label: el.name,
                            id: el.pk,
                            thumbnail: el.thumbnail
                        };
                    });
                    response(transformed);
                },
                error: function () {
                    response([]);
                }
            });
        },
        create: function () {
            $(this).data('ui-autocomplete')._renderItem = function (ul, item) {

                var html = `<a href='/part/${item.id}/'><span>`;

                html += `<img class='hover-img-thumb' src='`;
                html += item.thumbnail || `/static/img/blank_image.png`;
                html += `'> `;
                html += item.label;

                html += '</span></a>';

                return $('<li>').append(html).appendTo(ul);
            };
        },
        select: function( event, ui ) {
            window.location = '/part/' + ui.item.id + '/';
        },
        minLength: 2,
        classes: {'ui-autocomplete': 'dropdown-menu search-menu'},
    });
}

function isFileTransfer(transfer) {
    /* Determine if a transfer (e.g. drag-and-drop) is a file transfer 
     */

    return transfer.files.length > 0;
}


function enableDragAndDrop(element, url, options) {
    /* Enable drag-and-drop file uploading for a given element.
    
    Params:
        element - HTML element lookup string e.g. "#drop-div"
        url - URL to POST the file to
        options - object with following possible values:
            label - Label of the file to upload (default='file')
            data - Other form data to upload
            success - Callback function in case of success
            error - Callback function in case of error
            method - HTTP method
    */

    data = options.data || {};

    $(element).on('drop', function(event) {

        var transfer = event.originalEvent.dataTransfer;

        var label = options.label || 'file';

        var formData = new FormData();

        // Add the extra data
        for (var key in data) {
            formData.append(key, data[key]);
        }

        if (isFileTransfer(transfer)) {
            formData.append(label, transfer.files[0]);
            
            inventreeFormDataUpload(
                url,
                formData,
                {
                    success: function(data, status, xhr) {
                        console.log('Uploaded file via drag-and-drop');
                        if (options.success) {
                            options.success(data, status, xhr);
                        }
                    },
                    error: function(xhr, status, error) {
                        console.log('File upload failed');
                        if (options.error) {
                            options.error(xhr, status, error);
                        }
                    },
                    method: options.method || 'POST',
                }
            );
        } else {
            console.log('Ignoring drag-and-drop event (not a file)');
        }
    });
}


function inventreeSave(name, value) {
    /*
     * Save a key:value pair to local storage
     */

    var key = "inventree-" + name;
    localStorage.setItem(key, value);
}

function inventreeLoad(name, defaultValue) {
    /* 
     * Retrieve a key:value pair from local storage
     */

    var key = "inventree-" + name;

    var value = localStorage.getItem(key);

    if (value == null) {
        return defaultValue;
    } else {
        return value;
    }
}
