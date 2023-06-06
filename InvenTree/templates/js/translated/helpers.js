{% load i18n %}

/* globals
    EasyMDE,
    inventreeFormDataUpload,
    inventreeGet,
    inventreePut,
    showApiError,
    user_settings,
*/

/* exported
    blankImage,
    deleteButton,
    editButton,
    formatDecimal,
    imageHoverIcon,
    makeCopyButton,
    makeDeleteButton,
    makeEditButton,
    makeIconBadge,
    makeIconButton,
    makeInfoButton,
    makeProgressBar,
    makeRemoveButton,
    renderLink,
    sanitizeInputString,
    select2Thumbnail,
    setupNotesField,
    shortenString,
    thumbnailImage
    yesNoLabel,
    withTitle,
    wrapButtons,
    renderClipboard,
*/

/* exported
    makeIcon,
    trueFalseLabel,
    yesNoLabel,
*/


/*
 * Convert a value (which may be a string) to a boolean value
 *
 * @param {string} value: Input value
 * @returns {boolean} true or false
 */
function toBool(value) {

    if (typeof value == 'string') {

        if (value.length == 0) {
            return false;
        }

        value = value.toLowerCase();

        if (['true', 't', 'yes', 'y', '1', 'on', 'ok'].includes(value)) {
            return true;
        } else {
            return false;
        }
    } else {
        return value == true;
    }
}


function yesNoLabel(value, options={}) {
    let text = '';
    let color = '';

    if (toBool(value)) {
        text = options.pass || '{% trans "YES" %}';
        color = 'bg-success';
    } else {
        text = options.fail || '{% trans "NO" %}';
        color = 'bg-warning';
    }

    if (options.muted) {
        color = 'bg-secondary';
    }

    return `<span class='badge rounded-pill ${color}'>${text}</span>`;
}


function trueFalseLabel(value, options={}) {
    options.pass = '{% trans "True" %}';
    options.fail = '{% trans "False" %}';

    return yesNoLabel(value, options);
}


function editButton(url, text='{% trans "Edit" %}') {
    return `<button class='btn btn-success edit-button btn-sm' type='button' url='${url}'>${text}</button>`;
}


function deleteButton(url, text='{% trans "Delete" %}') {
    return `<button class='btn btn-danger delete-button btn-sm' type='button' url='${url}'>${text}</button>`;
}



/*
 * Ensure a string does not exceed a maximum length.
 * Useful for displaying long strings in tables,
 * to ensure a very long string does not "overflow" the table
 */
function shortenString(input_string, options={}) {

    // Maximum length can be provided via options argument, or via a user-configurable setting
    var max_length = options.max_length || user_settings.TABLE_STRING_MAX_LENGTH || 100;

    if (!max_length || !input_string) {
        return input_string;
    }

    input_string = input_string.toString();

    // Easy option: input string is already short enough
    if (input_string.length <= max_length) {
        return input_string;
    }

    var N = Math.floor(max_length / 2 - 1);

    var output_string = input_string.slice(0, N) + '...' + input_string.slice(-N);

    return output_string;
}


function withTitle(html, title, options={}) {

    return `<div title='${title}'>${html}</div>`;
}


/* Format a decimal (floating point) number, to strip trailing zeros
 */
function formatDecimal(number, places=5) {
    return +parseFloat(number).toFixed(places);
}


function blankImage() {
    return `/static/img/blank_image.png`;
}

/* Render a small thumbnail icon for an image.
 * On mouseover, display a full-size version of the image
 */
function imageHoverIcon(url) {

    if (!url) {
        url = blankImage();
    }

    var html = `
        <a class='hover-icon'>
            <img class='hover-img-thumb' src='${url}'>
            <img class='hover-img-large' src='${url}'>
        </a>
        `;

    return html;
}


/**
 * Renders a simple thumbnail image
 * @param {String} url is the image URL
 * @returns html <img> tag
 */
function thumbnailImage(url, options={}) {

    if (!url) {
        url = blankImage();
    }

    // TODO: Support insertion of custom classes
    var title = options.title || '';

    var html = `<img class='hover-img-thumb' src='${url}' title='${title}'>`;

    return html;

}


// Render a select2 thumbnail image
function select2Thumbnail(image) {
    if (!image) {
        image = blankImage();
    }

    return `<img src='${image}' class='select2-thumbnail'>`;
}


/*
 * Construct a simple FontAwesome icon span
 */
function makeIcon(icon, title='', options={}) {

    let classes = options.classes || 'fas';

    return `<span class='${classes} ${icon}' title='${title}'></span>`;
}


/*
 * Construct an 'icon badge' which floats to the right of an object
 */
function makeIconBadge(icon, title='', options={}) {

    let content = options.content || '';

    let html = `
    <span class='icon-badge fas ${icon} float-right' title='${title}'>
        ${content}
    </span>`;

    return html;
}


/*
 * Wrap list of buttons in a button group <div>
 */
function wrapButtons(buttons) {

    if (!buttons) {
        // Return empty element if no buttons are provided
        return '';
    }

    return `<div class='btn-group float-right' role='group'>${buttons}</div>`;
}


/*
 * Construct an 'icon button' using the fontawesome set
 */
function makeIconButton(icon, cls, pk, title, options={}) {

    var classes = `btn btn-outline-secondary ${cls}`;

    var id = `${cls}-${pk}`;

    var html = '';

    var extraProps = options.extra || '';

    var style = '';

    if (options.hidden) {
        style += `display: none;`;
    }

    if (options.disabled) {
        extraProps += `disabled='true' `;
    }

    if (options.collapseTarget) {
        extraProps += `data-bs-toggle='collapse' href='#${options.collapseTarget}'`;
    }

    html += `<button pk='${pk}' id='${id}' class='${classes}' title='${title}' ${extraProps} style='${style}'>`;
    html += `<span class='fas ${icon}'></span>`;
    html += `</button>`;

    return html;
}


/*
 * Helper function for making a common 'info' button
 */
function makeInfoButton(cls, pk, title, options={}) {
    return makeIconButton('fa-info-circle', cls, pk, title, options);
}


/*
 * Helper function for making a common 'edit' button
 */
function makeEditButton(cls, pk, title, options={}) {
    return makeIconButton('fa-edit icon-blue', cls, pk, title, options);
}


/*
 * Helper function for making a common 'copy' button
 */
function makeCopyButton(cls, pk, title, options={}) {
    return makeIconButton('fa-clone', cls, pk, title, options);
}


/*
 * Helper function for making a common 'delete' button
 */
function makeDeleteButton(cls, pk, title, options={}) {
    return makeIconButton('fa-trash-alt icon-red', cls, pk, title, options);
}


/*
 * Helper function for making a common 'remove' button
 */
function makeRemoveButton(cls, pk, title, options={}) {
    return makeIconButton('fa-times-circle icon-red', cls, pk, title, options);
}


/*
 * Render a progressbar!
 *
 * @param value is the current value of the progress bar
 * @param maximum is the maximum value of the progress bar
 */
function makeProgressBar(value, maximum, opts={}) {

    var options = opts || {};

    value = formatDecimal(parseFloat(value));

    var percent = 100;

    // Prevent div-by-zero or null value
    if (maximum && maximum > 0) {
        maximum = formatDecimal(parseFloat(maximum));
        percent = formatDecimal(parseInt(value / maximum * 100));
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

    var text = options.text;

    if (!text) {
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
    }

    var id = options.id || 'progress-bar';

    if (opts.max_width) {
        style += `max-width: ${options.max_width}; `;
    }

    return `
    <div id='${id}' class='progress' style='${style}'>
        <div class='progress-bar ${extraclass}' role='progressbar' aria-valuenow='${percent}' aria-valuemin='0' aria-valuemax='100' style='width:${percent}%'></div>
        <div class='progress-value'>${text}</div>
    </div>
    `;
}


/*
 * Render a URL for display
 */
function renderLink(text, url, options={}) {
    if (url === null || url === undefined || url === '') {
        return text;
    }

    var max_length = options.max_length || user_settings.TABLE_STRING_MAX_LENGTH || 100;

    if (max_length > 0) {
        text = shortenString(text, {
            max_length: max_length,
        });
    }

    var extras = '';

    if (options.tooltip != false) {
        extras += ` title="${url}"`;
    }

    if (options.download) {
        extras += ` download`;
    }

    let suffix = '';
    if (options.external) {
        extras += ` target="_blank" rel="noopener noreferrer"`;

        suffix = ` <i class="fas fa-external-link-alt fa-xs d-none d-xl-inline"></i>`;
    }
    return `<a href="${url}" ${extras}>${text}${suffix}</a>`;
}


/*
 * Configure an EasyMDE editor for the given element,
 * allowing markdown editing of the notes field.
 */
function setupNotesField(element, url, options={}) {

    var editable = options.editable || false;

    // Read initial notes value from the URL
    var initial = null;

    inventreeGet(url, {}, {
        async: false,
        success: function(response) {
            initial = response[options.notes_field || 'notes'];
        },
    });

    var toolbar_icons = [
        'preview', '|',
    ];

    if (editable) {
        // Heading icons
        toolbar_icons.push('heading-1', 'heading-2', 'heading-3', '|');

        // Font style
        toolbar_icons.push('bold', 'italic', 'strikethrough', '|');

        // Text formatting
        toolbar_icons.push('unordered-list', 'ordered-list', 'code', 'quote', '|');

        // Elements
        toolbar_icons.push('table', 'link', 'image');
    }

    // Markdown syntax guide
    toolbar_icons.push('|', 'guide');

    const mde = new EasyMDE({
        element: document.getElementById(element),
        initialValue: initial,
        toolbar: toolbar_icons,
        uploadImage: true,
        imagePathAbsolute: true,
        imageUploadFunction: function(imageFile, onSuccess, onError) {
            // Attempt to upload the image to the InvenTree server
            var form_data = new FormData();

            form_data.append('image', imageFile);

            inventreeFormDataUpload('{% url "api-notes-image-list" %}', form_data, {
                success: function(response) {
                    onSuccess(response.image);
                },
                error: function(xhr, status, error) {
                    onError(error);
                }
            });
        },
        shortcuts: [],
    });


    // Hide the toolbar
    $(`#${element}`).next('.EasyMDEContainer').find('.editor-toolbar').hide();

    if (!editable) {
        // Set readonly
        mde.codemirror.setOption('readOnly', true);

        // Hide the "edit" and "save" buttons
        $('#edit-notes').hide();
        $('#save-notes').hide();

    } else {
        mde.togglePreview();

        // Add callback for "edit" button
        $('#edit-notes').click(function() {
            $('#edit-notes').hide();
            $('#save-notes').show();

            // Show the toolbar
            $(`#${element}`).next('.EasyMDEContainer').find('.editor-toolbar').show();

            mde.togglePreview();
        });

        // Add callback for "save" button
        $('#save-notes').click(function() {

            var data = {};

            data[options.notes_field || 'notes'] = mde.value();

            $('#save-notes').find('#save-icon').removeClass('fa-save').addClass('fa-spin fa-spinner');

            inventreePut(url, data, {
                method: 'PATCH',
                success: function(response) {
                    $('#save-notes').find('#save-icon').removeClass('fa-spin fa-spinner').addClass('fa-check-circle');
                },
                error: function(xhr) {
                    $('#save-notes').find('#save-icon').removeClass('fa-spin fa-spinner').addClass('fa-times-circle icon-red');
                    showApiError(xhr, url);
                }
            });
        });
    }
}


/*
 * Sanitize a string provided by the user from an input field,
 * e.g. data form or search box
 *
 * - Remove leading / trailing whitespace
 * - Remove hidden control characters
 */
function sanitizeInputString(s, options={}) {

    if (!s) {
        return s;
    }

    // Remove ASCII control characters
    // eslint-disable-next-line no-control-regex
    s = s.replace(/[\x00-\x1F\x7F]+/g, '');

    // Remove Unicode control characters
    s = s.replace(/[\p{C}]+/gu, '');

    s = s.trim();

    return s;
}

/*
 * Inserts HTML data equal to clip.html into input string
 * Enables insertion of clipboard icons in dynamic tables
 *
 * clipString relies on ClipboardJS in the same manner as clip.html
 * Thus, this functionality will break if the call to
 * attachClipboard('.clip-btn') in script/inventree/inventree.js is altered
 */
function renderClipboard(s, prepend=false) {
    if (!s || typeof s != 'string') {
        return s;
    }

    let clipString = `<span class="d-none d-xl-inline"><button class="btn clip-btn" type="button" data-bs-toggle='tooltip' title='{% trans "copy to clipboard" %}'><em class="fas fa-copy"></em></button></span>`;

    if (prepend === true) {
        return `<div class="flex-cell">${clipString+s}</div>`;
    } else {
        return `<div class="flex-cell">${s+clipString}</div>`;
    }
}
