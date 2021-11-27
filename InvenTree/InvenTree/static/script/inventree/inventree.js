/* globals
    ClipboardJS,
    inventreeFormDataUpload,
    inventreeGet,
    launchModalForm,
    user_settings,
*/

/* exported
    attachClipboard,
    enableDragAndDrop,
    exportFormatOptions,
    inventreeDocReady,
    inventreeLoad,
    inventreeSave,
*/

function attachClipboard(selector, containerselector, textElement) {
    // set container
    if (containerselector) {
        containerselector = document.getElementById(containerselector);
    } else {
        containerselector = document.body;
    }

    var text = null;

    // set text-function
    if (textElement) {
        text = function() {
            return document.getElementById(textElement).textContent;
        };
    } else {
        text = function(trigger) {
            var content = trigger.parentElement.parentElement.textContent;
            return content.trim();
        };
    }

    // create Clipboard
    // eslint-disable-next-line no-unused-vars
    var cis = new ClipboardJS(selector, {
        text: text,
        container: containerselector
    });
}


/**
 * Return a standard list of export format options * 
 */
function exportFormatOptions() {
    return [
        {
            value: 'csv',
            display_name: 'CSV',
        },
        {
            value: 'tsv',
            display_name: 'TSV',
        },
        {
            value: 'xls',
            display_name: 'XLS',
        },
        {
            value: 'xlsx',
            display_name: 'XLSX',
        },
    ];
}


function inventreeDocReady() {
    /* Run this function when the HTML document is loaded.
     * This will be called for every page that extends "base.html"
     */

    window.addEventListener('dragover', function(e) {
        e = e || event;
        e.preventDefault();
    }, false);

    window.addEventListener('drop', function(e) {
        e = e || event;
        e.preventDefault();
    }, false);

    /* Add drag-n-drop functionality to any element
     * marked with the class 'dropzone'
     */
    $('.dropzone').on('dragenter', function(event) {

        // TODO - Only indicate that a drop event will occur if a file is being dragged
        var transfer = event.originalEvent.dataTransfer;

        // eslint-disable-next-line no-constant-condition
        if (true || isFileTransfer(transfer)) {
            $(this).addClass('dragover');
        }
    });

    $('.dropzone').on('dragleave drop', function() {
        $(this).removeClass('dragover');
    });

    // Callback to launch the 'About' window
    $('#launch-about').click(function() {
        var modal = $('#modal-about');

        modal.modal({
            backdrop: 'static',
            keyboard: true,
        });

        modal.modal('show');
    });

    // Callback to launch the 'Database Stats' window
    $('#launch-stats').click(function() {
        launchModalForm('/stats/', {
            no_post: true,
        });
    });

    // Initialize clipboard-buttons
    attachClipboard('.clip-btn');
    attachClipboard('.clip-btn', 'modal-about');
    attachClipboard('.clip-btn-version', 'modal-about', 'about-copy-text');

    // Add autocomplete to the search-bar
    if ($('#search-bar').exists()) {
        $('#search-bar').autocomplete({
            source: function(request, response) {

                var params = {
                    search: request.term,
                    limit: user_settings.SEARCH_PREVIEW_RESULTS,
                    offset: 0,
                };

                if (user_settings.SEARCH_HIDE_INACTIVE_PARTS) {
                    // Limit to active parts
                    params.active = true;
                }

                $.ajax({
                    url: '/api/part/',
                    data: params,
                    success: function(data) {

                        var transformed = $.map(data.results, function(el) {
                            return {
                                label: el.full_name,
                                id: el.pk,
                                thumbnail: el.thumbnail,
                                data: el,
                            };
                        });
                        response(transformed);
                    },
                    error: function() {
                        response([]);
                    }
                });
            },
            create: function() {
                $(this).data('ui-autocomplete')._renderItem = function(ul, item) {

                    var html = `
                    <div class='search-autocomplete-item' title='${item.data.description}'>
                        <a href='/part/${item.id}/'>
                            <span style='padding-right: 10px;'><img class='hover-img-thumb' src='${item.thumbnail || "/static/img/blank_image.png"}'> ${item.label}</span>
                        </a>
                        <span class='flex' style='flex-grow: 1;'></span>
                    `;
                    
                    if (user_settings.SEARCH_SHOW_STOCK_LEVELS) {
                        html += partStockLabel(
                            item.data,
                            {
                                classes: 'badge-right',
                            }
                        );
                    }

                    html += '</div>';

                    return $('<li>').append(html).appendTo(ul);
                };
            },
            select: function( event, ui ) {
                window.location = '/part/' + ui.item.id + '/';
            },
            minLength: 2,
            classes: {
                'ui-autocomplete': 'dropdown-menu search-menu',
            },
            position: {
                my : "right top",
                at: "right bottom"
            }
        });
    }

    // Generate brand-icons
    $('.brand-icon').each(function(i, obj) {
        loadBrandIcon($(this), $(this).attr('brand_name'));
    });

    // Callback for "admin view" button
    $('#admin-button, .admin-button').click(function() {
        var url = $(this).attr('url');

        location.href = url;
    });

    // Display any cached alert messages
    showCachedAlerts();

    // Start notification background worker to check every 5 seconds if notifications are available
    var notificationRunner = setInterval(notificationCheck, 5000);
}


/**
 * The notification checker is initiated when the doc is loaded. It checks if there are unread notifications
 * if unread messages exist the alert flag is raised by making it visible
 **/
var current_alert_state = false;
function notificationCheck() {
    inventreeGet(
        '/api/notifications/',
        {
            read: false,
        },
        {
            success: function(response) {
                if (response.length == 0) {
                    if (current_alert_state == true){
                        $("#notification-alert").addClass("d-none");
                        current_alert_state = false;
                    }
                } else {
                    if (current_alert_state == false){
                        $("#notification-alert").removeClass("d-none");
                        current_alert_state = true;
                    }
                }
            }
        }
    );
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

    var data = options.data || {};

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


/**
 * Save a key:value pair to local storage
 * @param {String} name - settting key 
 * @param {String} value - setting value
 */
function inventreeSave(name, value) {

    var key = `inventree-${name}`;
    localStorage.setItem(key, value);
}


/**
 * Retrieve a key:value pair from local storage
 * @param {*} name - setting key
 * @param {*} defaultValue - default value (returned if no matching key:value pair is found)
 * @returns 
 */
function inventreeLoad(name, defaultValue) {

    var key = `inventree-${name}`;

    var value = localStorage.getItem(key);

    if (value == null) {
        return defaultValue;
    } else {
        return value;
    }
}

function loadBrandIcon(element, name) {
    // check if icon exists
    var icon = window.FontAwesome.icon({prefix: 'fab', iconName: name});

    if (icon) {
        // add icon to button
        element.addClass('fab fa-' + name);
    }
}

// Convenience function to determine if an element exists
$.fn.exists = function() {
    return this.length !== 0;
};
