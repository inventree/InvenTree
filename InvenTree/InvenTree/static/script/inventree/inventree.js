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
    sanitizeData,
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
    new ClipboardJS(selector, {
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
        launchModalForm(`/about/`, {
            no_post: true,
            after_render: function() {
                attachClipboard('.clip-btn', 'modal-form', 'about-copy-text');
            }
        });
    });

    // Callback to launch the 'Database Stats' window
    $('#launch-stats').click(function() {
        launchModalForm('/stats/', {
            no_post: true,
        });
    });

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

    // start watcher
    startNotificationWatcher();

    // always refresh when the focus returns
    $(document).focus(function(){
        startNotificationWatcher();
    });

    // kill notification watcher if focus is lost -> respect your users cycles
    $(document).blur(function(){
        stopNotificationWatcher();
    });

    // Calbacks for search panel
    $('#offcanvas-search').on('shown.bs.offcanvas', openSearchPanel);
    $('#offcanvas-search').on('hidden.bs.offcanvas', closeSearchPanel);

    // Callbacks for notifications panel
    $('#offcanvas-notification').on('show.bs.offcanvas', openNotificationPanel);  // listener for opening the notification panel
    $('#offcanvas-notification').on('hidden.bs.offcanvas', closeNotificationPanel);  // listener for closing the notification panel
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


/*
 * Function to sanitize a (potentially nested) object.
 * Iterates through all levels, and sanitizes each primitive string.
 *
 * Note that this function effectively provides a "deep copy" of the provided data,
 * and the original data structure is unaltered.
 */
function sanitizeData(data) {
    if (data == null) {
        return null;
    } else if (Array.isArray(data)) {
        // Handle arrays
        var arr = [];
        data.forEach(function(val) {
            arr.push(sanitizeData(val));
        });

        return arr;
    } else if (typeof(data) === 'object') {
        // Handle nested structures
        var nested = {};
        $.each(data, function(k, v) {
            nested[k] = sanitizeData(v);
        });

        return nested;
    } else if (typeof(data) === 'string') {
        // Perform string replacement
        return data.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;').replace(/`/g, '&#x60;');
    } else {
        return data;
    }
}


// Convenience function to determine if an element exists
$.fn.exists = function() {
    return this.length !== 0;
};
