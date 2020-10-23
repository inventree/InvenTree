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

    var url = transfer.getData('text/html').match(/src\s*=\s*"(.+?)"/)[1];

    console.log('Image URL: ' + url);

    return url;
}

function makeIconBadge(icon, title) {
    // Construct an 'icon badge' which floats to the right of an object

    var html = `<span class='fas ${icon} label-right' title='${title}'></span>`;

    return html;
}

function makeIconButton(icon, cls, pk, title, options={}) {
    // Construct an 'icon button' using the fontawesome set

    var classes = `btn btn-default btn-glyph ${cls}`;

    var id = `${cls}-${pk}`;

    var html = '';

    var extraProps = '';

    if (options.disabled) {
        extraProps += "disabled='true' ";
    }
    
    html += `<button pk='${pk}' id='${id}' class='${classes}' title='${title}' ${extraProps}>`;
    html += `<span class='fas ${icon}'></span>`;
    html += `</button>`;

    return html;
}

function makeProgressBar(value, maximum, opts={}) {
    /*
     * Render a progessbar!
     * 
     * @param value is the current value of the progress bar
     * @param maximum is the maximum value of the progress bar
     */

    var options = opts || {};

    value = parseFloat(value);

    var percent = 100;

    // Prevent div-by-zero or null value
    if (maximum && maximum > 0) {
        maximum = parseFloat(maximum);
        percent = parseInt(value / maximum * 100);
    }

    if (percent > 100) {
        percent = 100;
    }

    var extraclass = '';

    if (value > maximum) {
        extraclass='progress-bar-over';
    } else if (value < maximum) {
        extraclass = 'progress-bar-under';
    }

    var style = options.style || '';

    var text = '';

    if (style == 'percent') {
        // Display e.g. "50%"

        text = `${percent}%`;
    } else if (style == 'max') {
        // Display just the maximum value
        text = `${maximum}`;
    } else if (style == 'value') {
        // Display just the current value
        text = `${value}`;
    } else if (style == 'blank') {
        // No display!
        text = '';
    } else {
        /* Default style
        * Display e.g. "5 / 10"
        */

        text = `${value} / ${maximum}`;
    }

    var id = options.id || 'progress-bar';

    return `
    <div id='${id}' class='progress'>
        <div class='progress-bar ${extraclass}' role='progressbar' aria-valuenow='${percent}' aria-valuemin='0' aria-valuemax='100' style='width:${percent}%'></div>
        <div class='progress-value'>${text}</div>
    </div>
    `;
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
                    }
                }
            );
        } else {
            console.log('Ignoring drag-and-drop event (not a file)');
        }
    });
}

function imageHoverIcon(url) {
    /* Render a small thumbnail icon for an image.
     * On mouseover, display a full-size version of the image
     */

    if (!url) {
        url = '/static/img/blank_image.png';
    }

    var html = `
        <a class='hover-icon'>
            <img class='hover-img-thumb' src='` + url + `'>
            <img class='hover-img-large' src='` + url + `'>
        </a>
        `;

    return html;
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

function inventreeLoadInt(name) {
    /*
     * Retrieve a value from local storage, and attempt to cast to integer
     */

    var data = inventreeLoad(name);

    return parseInt(data, 10);
}

function inventreeLoadFloat(name) {

    var data = inventreeLoad(name);

    return parseFloat(data);
}

function inventreeDel(name) {

    var key = 'inventree-' + name;

    localStorage.removeItem(key);
}