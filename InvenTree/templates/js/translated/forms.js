{% load i18n %}
{% load inventree_extras %}

/* globals
    createNewModal,
    inventreeFormDataUpload,
    inventreeGet,
    inventreePut,
    global_settings,
    modalEnable,
    modalShowSubmitButton,
    renderBuild,
    renderCompany,
    renderManufacturerPart,
    renderOwner,
    renderPart,
    renderPartCategory,
    renderPartParameterTemplate,
    renderStockItem,
    renderStockLocation,
    renderSupplierPart,
    renderUser,
    showAlertOrCache,
    showApiError,
*/

/* exported
    clearFormInput,
    disableFormInput,
    enableFormInput,
    hideFormInput,
    setFormInputPlaceholder,
    setFormGroupVisibility,
    showFormInput,
    selectImportFields,
*/

/**
 *
 * This file contains code for rendering (and managing) HTML forms
 * which are served via the django-drf API.
 *
 * The django DRF library provides an OPTIONS method for each API endpoint,
 * which allows us to introspect the available fields at any given endpoint.
 *
 * The OPTIONS method provides the following information for each available field:
 *
 * - Field name
 * - Field label (translated)
 * - Field help text (translated)
 * - Field type
 * - Read / write status
 * - Field required status
 * - min_value / max_value
 *
 */

// Set global default theme for select2
$.fn.select2.defaults.set('theme', 'bootstrap-5');

/*
 * Return true if the OPTIONS specify that the user
 * can perform a GET method at the endpoint.
 */
function canView(OPTIONS) {

    if ('actions' in OPTIONS) {
        return ('GET' in OPTIONS.actions);
    } else {
        return false;
    }
}


/*
 * Return true if the OPTIONS specify that the user
 * can perform a POST method at the endpoint
 */
function canCreate(OPTIONS) {

    if ('actions' in OPTIONS) {
        return ('POST' in OPTIONS.actions);
    } else {
        return false;
    }
}


/*
 * Return true if the OPTIONS specify that the user
 * can perform a PUT or PATCH method at the endpoint
 */
function canChange(OPTIONS) {

    if ('actions' in OPTIONS) {
        return ('PUT' in OPTIONS.actions || 'PATCH' in OPTIONS.actions);
    } else {
        return false;
    }
}


/*
 * Return true if the OPTIONS specify that the user
 * can perform a DELETE method at the endpoint
 */
function canDelete(OPTIONS) {

    if ('actions' in OPTIONS) {
        return ('DELETE' in OPTIONS.actions);
    } else {
        return false;
    }
}


/*
 * Get the API endpoint options at the provided URL,
 * using a HTTP options request.
 */
function getApiEndpointOptions(url, callback) {

    if (!url) {
        return;
    }

    // Include extra context information in the request
    url += '?context=true';

    // Return the ajax request object
    $.ajax({
        url: url,
        type: 'OPTIONS',
        contentType: 'application/json',
        dataType: 'json',
        accepts: {
            json: 'application/json',
        },
        success: callback,
        error: function(xhr) {
            // TODO: Handle error
            console.error(`Error in getApiEndpointOptions at '${url}'`);
            showApiError(xhr, url);
        }
    });
}


/*
 * Construct a 'creation' (POST) form, to create a new model in the database.
 *
 * arguments:
 * - fields: The 'actions' object provided by the OPTIONS endpoint
 *
 * options:
 * -
 */
function constructCreateForm(fields, options) {

    // Check if default values were provided for any fields
    for (const name in fields) {

        var field = fields[name];

        var field_options = options.fields[name] || {};

        // If a 'value' is not provided for the field,
        if (field.value == null) {

            if ('value' in field_options) {
                // Client has specified the default value for the field
                field.value = field_options.value;
            } else if (field.default != null) {
                // OPTIONS endpoint provided default value for this field
                field.value = field.default;
            }
        }
    }

    // We should have enough information to create the form!
    constructFormBody(fields, options);
}


/*
 * Construct a 'change' (PATCH) form, to create a new model in the database.
 *
 * arguments:
 * - fields: The 'actions' object provided by the OPTIONS endpoint
 *
 * options:
 * -
 */
function constructChangeForm(fields, options) {

    // Request existing data from the API endpoint
    $.ajax({
        url: options.url,
        data: options.params || {},
        type: 'GET',
        contentType: 'application/json',
        dataType: 'json',
        accepts: {
            json: 'application/json',
        },
        success: function(data) {

            // Ensure the data are fully sanitized before we operate on it
            data = sanitizeData(data);

            // An optional function can be provided to process the returned results,
            // before they are rendered to the form
            if (options.processResults) {
                var processed = options.processResults(data, fields, options);

                // If the processResults function returns data, it will be stored
                if (processed) {
                    data = processed;
                }
            }

            // Push existing 'value' to each field
            for (const field in data) {

                if (field in fields) {
                    fields[field].value = data[field];
                }
            }

            // Store the entire data object
            options.instance = data;

            constructFormBody(fields, options);
        },
        error: function(xhr) {
            // TODO: Handle error here
            console.error(`Error in constructChangeForm at '${options.url}'`);

            showApiError(xhr, options.url);
        }
    });
}


/*
 * Construct a 'delete' form, to remove a model instance from the database.
 *
 * arguments:
 * - fields: The 'actions' object provided by the OPTIONS request
 * - options: The 'options' object provided by the client
 */
function constructDeleteForm(fields, options) {

    // If we are deleting a specific "instance" (i.e. a single object)
    // then we request the instance information first

    // However we may be performing a "multi-delete" (against a list endpoint),
    // in which case we do not want to perform such a request!

    if (options.multi_delete) {
        constructFormBody(fields, options);
    } else {
        // Request existing data from the API endpoint
        // This data can be used to render some information on the form
        $.ajax({
            url: options.url,
            type: 'GET',
            contentType: 'application/json',
            dataType: 'json',
            accepts: {
                json: 'application/json',
            },
            success: function(data) {

                // Store the instance data
                options.instance = data;

                constructFormBody(fields, options);
            },
            error: function(xhr) {
                // TODO: Handle error here
                console.error(`Error in constructDeleteForm at '${options.url}`);

                showApiError(xhr, options.url);
            }
        });
    }
}


/*
 * Request API OPTIONS data from the server,
 * and construct a modal form based on the response.
 *
 * url: API URL which defines form data
 * options:
 * - method: The HTTP method e.g. 'PUT', 'POST', 'DELETE' (default='PATCH')
 * - title: The form title
 * - submitText: Text for the "submit" button
 * - submitClass: CSS class for the "submit" button (default = ')
 * - closeText: Text for the "close" button
 * - fields: list of fields to display, with the following options
 *      - filters: API query filters
 *      - onEdit: callback when field is edited
 *      - secondary: Define a secondary modal form for this field
 *      - label: Specify custom label
 *      - help_text: Specify custom help_text
 *      - placeholder: Specify custom placeholder text
 *      - value: Specify initial value
 *      - hidden: Set to true to hide the field
 *      - icon: font-awesome icon to display before the field
 *      - prefix: Custom HTML prefix to display before the field
 * - data: map of data to fill out field values with
 * - focus: Name of field to focus on when modal is displayed
 * - preventClose: Set to true to prevent form from closing on success
 * - onSuccess: callback function when form action is successful
 * - follow: If a 'url' is provided by the API on success, redirect to it
 * - redirect: A URL to redirect to after form success
 * - reload: Set to true to reload the current page after form success
 * - confirm: Set to true to require a "confirm" button
 * - confirmText: Text for confirm button (default = "Confirm")
 *
 */
function constructForm(url, options) {

    // An "empty" form will be defined locally
    if (url == null) {
        constructFormBody({}, options);
    }

    // Save the URL
    options.url = url;

    // Default HTTP method
    options.method = options.method || 'PATCH';

    // Default "groups" definition
    options.groups = options.groups || {};
    options.current_group = null;

    // Construct an "empty" data object if not provided
    if (!options.data) {
        options.data = {};
    }

    // Request OPTIONS endpoint from the API
    getApiEndpointOptions(url, function(OPTIONS) {

        // Extract any custom 'context' information from the OPTIONS data
        options.context = OPTIONS.context || {};

        // Construct fields (can be a static parameter or a function)
        if (options.fieldsFunction) {
            options.fields = options.fieldsFunction(options);
        } else {
            options.fields = options.fields || {};
        }

        /*
         * Determine what "type" of form we want to construct,
         * based on the requested action.
         *
         * First we must determine if the user has the correct permissions!
         */

        switch (options.method) {
        case 'POST':
            if (canCreate(OPTIONS)) {
                constructCreateForm(OPTIONS.actions.POST, options);
            } else {
                // User does not have permission to POST to the endpoint
                showMessage('{% trans "Action Prohibited" %}', {
                    style: 'danger',
                    details: '{% trans "Create operation not allowed" %}',
                    icon: 'fas fa-user-times',
                });

                console.warn(`'POST action unavailable at ${url}`);
            }
            break;
        case 'PUT':
        case 'PATCH':
            if (canChange(OPTIONS)) {
                constructChangeForm(OPTIONS.actions.PUT, options);
            } else {
                // User does not have permission to PUT/PATCH to the endpoint
                showMessage('{% trans "Action Prohibited" %}', {
                    style: 'danger',
                    details: '{% trans "Update operation not allowed" %}',
                    icon: 'fas fa-user-times',
                });

                console.warn(`${options.method} action unavailable at ${url}`);
            }
            break;
        case 'DELETE':
            if (canDelete(OPTIONS)) {
                constructDeleteForm(OPTIONS.actions.DELETE, options);
            } else {
                // User does not have permission to DELETE to the endpoint
                showMessage('{% trans "Action Prohibited" %}', {
                    style: 'danger',
                    details: '{% trans "Delete operation not allowed" %}',
                    icon: 'fas fa-user-times',
                });

                console.warn(`DELETE action unavailable at ${url}`);
            }
            break;
        case 'GET':
            if (canView(OPTIONS)) {
                // TODO?
            } else {
                // User does not have permission to GET to the endpoint
                showMessage('{% trans "Action Prohibited" %}', {
                    style: 'danger',
                    details: '{% trans "View operation not allowed" %}',
                    icon: 'fas fa-user-times',
                });

                console.warn(`GET action unavailable at ${url}`);
            }
            break;
        default:
            console.warn(`constructForm() called with invalid method '${options.method}'`);
            break;
        }
    });
}


/*
 * Construct a modal form based on the provided options
 *
 * arguments:
 * - fields: The endpoint description returned from the OPTIONS request
 * - options: form options object provided by the client.
 */
function constructFormBody(fields, options) {

    var html = '';

    // Client must provide set of fields to be displayed,
    // otherwise *all* fields will be displayed
    var displayed_fields = options.fields || fields;

    // Override default option values if a 'DELETE' form is specified
    if (options.method == 'DELETE') {
        if (!('confirm' in options)) {
            options.confirm = true;
        }

        if (!('submitClass' in options)) {
            options.submitClass = 'danger';
        }

        if (!('submitText' in options)) {
            options.submitText = '{% trans "Delete" %}';
        }
    }

    // Handle initial data overrides
    if (options.data) {
        for (const field in options.data) {

            if (field in fields) {
                fields[field].value = options.data[field];
            }
        }
    }

    // Initialize an "empty" field for each specified field
    for (field in displayed_fields) {
        if (!(field in fields)) {
            fields[field] = {};
        }
    }

    // Provide each field object with its own name
    for (field in fields) {
        fields[field].name = field;

        // If any "instance_filters" are defined for the endpoint, copy them across (overwrite)
        if (fields[field].instance_filters) {
            fields[field].filters = Object.assign(fields[field].filters || {}, fields[field].instance_filters);
        }

        var field_options = displayed_fields[field];

        // Copy custom options across to the fields object
        if (field_options) {

            // Override existing query filters (if provided!)
            fields[field].filters = Object.assign(fields[field].filters || {}, field_options.filters);

            for (var opt in field_options) {

                var val = field_options[opt];

                if (opt == 'filters') {
                    // ignore filters (see above)
                } else if (opt == 'icon') {
                    // Specify custom icon
                    fields[field].prefix = `<span class='fas ${val}'></span>`;
                } else {
                    fields[field][opt] = field_options[opt];
                }
            }
        }
    }

    // Construct an ordered list of field names
    var field_names = [];

    for (var name in displayed_fields) {

        field_names.push(name);

        // Field not specified in the API, but the client wishes to add it!
        if (!(name in fields)) {
            fields[name] = displayed_fields[name];
        }
    }

    // Push the ordered field names into the options,
    // allowing successive functions to access them.
    options.field_names = field_names;

    // Render selected fields

    for (var idx = 0; idx < field_names.length; idx++) {

        var field_name = field_names[idx];

        var field = fields[field_name];

        switch (field.type) {
        // Skip field types which are simply not supported
        case 'nested object':
            continue;
        default:
            break;
        }

        html += constructField(field_name, field, options);
    }

    if (options.current_group) {
        // Close out the current group
        html += `</div></div>`;
    }

    // Create a new modal if one does not exists
    if (!options.modal) {
        options.modal = createNewModal(options);
    }

    var modal = options.modal;

    modalEnable(modal, true);

    // Insert generated form content
    $(modal).find('#form-content').html(html);

    if (options.preFormContent) {

        if (typeof(options.preFormContent) === 'function') {
            var content = options.preFormContent(options);
        } else {
            var content = options.preFormContent;
        }

        $(modal).find('#pre-form-content').html(content);
    }

    if (options.postFormContent) {
        $(modal).find('#post-form-content').html(options.postFormContent);
    }

    // Clear any existing buttons from the modal
    $(modal).find('#modal-footer-buttons').html('');

    // Insert "confirm" button (if required)
    if (options.confirm && global_settings.INVENTREE_REQUIRE_CONFIRM) {
        insertConfirmButton(options);
    }

    // Insert "persist" button (if required)
    if (options.persist) {
        insertPersistButton(options);
    }

    // Insert secondary buttons (if required)
    if (options.buttons) {
        insertSecondaryButtons(options);
    }

    // Display the modal
    $(modal).modal('show');

    updateFieldValues(fields, options);

    // Setup related fields
    initializeRelatedFields(fields, options);

    // Attach edit callbacks (if required)
    addFieldCallbacks(fields, options);

    // Attach clear callbacks (if required)
    addClearCallbacks(fields, options);

    modalShowSubmitButton(modal, true);

    $(modal).on('click', '#modal-form-submit', function() {

        // Immediately disable the "submit" button,
        // to prevent the form being submitted multiple times!
        enableSubmitButton(options, false);

        // Run custom code before normal form submission
        if (options.beforeSubmit) {
            options.beforeSubmit(fields, options);
        }

        // Run custom code instead of normal form submission
        if (options.onSubmit) {
            options.onSubmit(fields, options);
        } else {
            submitFormData(fields, options);
        }
    });

    initializeGroups(fields, options);

    if (options.afterRender) {
        // Custom callback function after form rendering
        options.afterRender(fields, options);
    }

    // Scroll to the top
    $(options.modal).find('.modal-form-content-wrapper').scrollTop(0);
}


// Add a "confirm" checkbox to the modal
// The "submit" button will be disabled unless "confirm" is checked
function insertConfirmButton(options) {

    var message = options.confirmMessage || '{% trans "Confirm" %}';

    var html = `
    <div class="form-check form-switch">
        <input class="form-check-input" type="checkbox" id="modal-confirm">
        <label class="form-check-label" for="modal-confirm">${message}</label>
    </div>
    `;

    $(options.modal).find('#modal-footer-buttons').append(html);

    // Disable the 'submit' button
    enableSubmitButton(options, false);

    // Trigger event
    $(options.modal).find('#modal-confirm').change(function() {
        var enabled = this.checked;

        enableSubmitButton(options, enabled);
    });
}


/* Add a checkbox to select if the modal will stay open after success */
function insertPersistButton(options) {

    var message = options.persistMessage || '{% trans "Keep this form open" %}';

    var html = `
    <div class="form-check form-switch">
        <input class="form-check-input" type="checkbox" id="modal-persist">
        <label class="form-check-label" for="modal-persist">${message}</label>
    </div>
    `;

    $(options.modal).find('#modal-footer-buttons').append(html);
}

/*
 * Add secondary buttons to the left of the close and submit buttons
 * with callback functions
 */
function insertSecondaryButtons(options) {
    for (var idx = 0; idx < options.buttons.length; idx++) {

        var html = `
        <button type="button" class="btn btn-outline-secondary" id="modal-form-${options.buttons[idx].name}">
            ${options.buttons[idx].title}
        </button>
        `;

        $(options.modal).find('#modal-footer-secondary-buttons').append(html);

        if (options.buttons[idx].onClick instanceof Function) {
            // Copy callback reference to prevent errors if `idx` changes value before execution
            var onclick_callback = options.buttons[idx].onClick;

            $(options.modal).find(`#modal-form-${options.buttons[idx].name}`).click(function() {
                onclick_callback(options);
            });
        }
    }
}

/*
 * Extract all specified form values as a single object
 */
function extractFormData(fields, options) {

    var data = {};

    for (var idx = 0; idx < options.field_names.length; idx++) {

        var name = options.field_names[idx];

        var field = fields[name] || null;

        if (!field) continue;

        if (field.type == 'candy') continue;

        data[name] = getFormFieldValue(name, field, options);
    }

    return data;
}


/*
 * Submit form data to the server.
 *
 */
function submitFormData(fields, options) {

    // Form data to be uploaded to the server
    // Only used if file / image upload is required
    var form_data = new FormData();

    // We can (optionally) provide a "starting point" for the submitted data
    var data = options.form_data || {};

    var has_files = false;

    var data_valid = true;

    var data_errors = {};

    // Extract values for each field
    for (var idx = 0; idx < options.field_names.length; idx++) {

        var name = options.field_names[idx];

        var field = fields[name] || null;

        // Ignore visual fields
        if (field && field.type == 'candy') continue;

        if (field) {

            switch (field.type) {
            // Ensure numerical fields are "valid"
            case 'integer':
            case 'float':
            case 'decimal':
                if (!validateFormField(name, options)) {
                    data_valid = false;

                    data_errors[name] = ['{% trans "Enter a valid number" %}'];
                }
                break;
            default:
                break;
            }

            var value = getFormFieldValue(name, field, options);

            // Handle file inputs
            if (field.type == 'image upload' || field.type == 'file upload') {

                var field_el = $(options.modal).find(`#id_${name}`)[0];

                var field_files = field_el.files;

                if (field_files.length > 0) {
                    // One file per field, please!
                    var file = field_files[0];

                    form_data.append(name, file);

                    has_files = true;
                }
            } else {

                // Normal field (not a file or image)
                form_data.append(name, value);

                data[name] = value;
            }
        } else {
            console.warn(`Could not find field matching '${name}'`);
        }
    }

    if (!data_valid) {
        handleFormErrors(data_errors, fields, options);
        return;
    }

    var upload_func = inventreePut;

    if (has_files) {
        upload_func = inventreeFormDataUpload;
        data = form_data;
    }

    // Optionally pre-process the data before uploading to the server
    if (options.processBeforeUpload) {
        data = options.processBeforeUpload(data);
    }

    // Show the progress spinner
    showModalSpinner(options.modal);

    // Submit data
    upload_func(
        options.url,
        data,
        {
            method: options.method,
            success: function(response) {
                $(options.modal).find('#modal-progress-spinner').hide();
                handleFormSuccess(response, options);
            },
            error: function(xhr) {

                $(options.modal).find('#modal-progress-spinner').hide();

                switch (xhr.status) {
                case 400:
                    handleFormErrors(xhr.responseJSON, fields, options);
                    break;
                default:
                    $(options.modal).modal('hide');

                    console.error(`Upload error at ${options.url}`);
                    showApiError(xhr, options.url);
                    break;
                }
            }
        }
    );
}


/*
 * Update (set) the field values based on the specified data.
 *
 * Iterate through each of the displayed fields,
 * and set the 'val' attribute of each one.
 *
 */
function updateFieldValues(fields, options) {

    for (var idx = 0; idx < options.field_names.length; idx++) {

        var name = options.field_names[idx];

        var field = fields[name] || null;

        if (field == null) {
            continue;
        }

        var value = field.value;

        if (value == null) {
            value = field.default;
        }

        if (value == null) {
            continue;
        }

        updateFieldValue(name, value, field, options);
    }
}

/*
 * Update the value of a named field
 */
function updateFieldValue(name, value, field, options) {

    var el = getFormFieldElement(name, options);

    if (!el) {
        console.warn(`updateFieldValue could not find field '${name}'`);
        return;
    }

    switch (field.type) {
    case 'boolean':
        if (value == true || value.toString().toLowerCase() == 'true') {
            el.prop('checked');
        }
        break;
    case 'related field':
        // Clear?
        if (value == null && !field.required) {
            el.val(null).trigger('change');
        }
        // TODO - Specify an actual value!
        break;
    case 'file upload':
    case 'image upload':
        break;
    default:
        el.val(value);
        break;
    }
}


// Find the named field element in the modal DOM
function getFormFieldElement(name, options) {

    var field_name = getFieldName(name, options);

    var el = null;

    if (options && options.modal) {
        // Field element is associated with a model?
        el = $(options.modal).find(`#id_${field_name}`);
    } else {
        // Field element is top-level
        el = $(`#id_${field_name}`);
    }

    if (!el.exists()) {
        console.error(`Could not find form element for field '${name}'`);
    }

    return el;
}


/*
 * Check that a "numerical" input field has a valid number in it.
 * An invalid number is expunged at the client side by the getFormFieldValue() function,
 * which means that an empty string '' is sent to the server if the number is not valid.
 * This can result in confusing error messages displayed under the form field.
 *
 * So, we can invalid numbers and display errors *before* the form is submitted!
 */
function validateFormField(name, options) {

    if (getFormFieldElement(name, options)) {

        var field_name = getFieldName(name, options);
        var el = document.getElementById(`id_${field_name}`);

        if (el.validity.valueMissing) {
            // Accept empty strings (server will validate)
            return true;
        } else {
            return el.validity.valid;
        }
    } else {
        return false;
    }

}


/*
 * Extract and field value before sending back to the server
 *
 * arguments:
 * - name: The name of the field
 * - field: The field specification provided from the OPTIONS request
 * - options: The original options object provided by the client
 */
function getFormFieldValue(name, field={}, options={}) {

    // Find the HTML element
    var el = getFormFieldElement(name, options);

    if (!el.exists()) {
        console.error(`getFormFieldValue could not locate field '${name}'`);
        return null;
    }

    var value = null;

    switch (field.type) {
    case 'boolean':
        value = el.is(':checked');
        break;
    case 'date':
    case 'datetime':
        value = el.val();

        // Ensure empty values are sent as nulls
        if (!value || value.length == 0) {
            value = null;
        }
        break;
    case 'string':
    case 'url':
    case 'email':
        value = sanitizeInputString(el.val());
        break;
    default:
        value = el.val();
        break;
    }

    return value;
}


/*
 * Handle successful form posting
 *
 * arguments:
 * - response: The JSON response object from the server
 * - options: The original options object provided by the client
 */
function handleFormSuccess(response, options) {

    // Display any required messages
    // Should we show alerts immediately or cache them?
    var cache = (options.follow && response.url) || options.redirect || options.reload;

    // Should the form "persist"?
    var persist = false;

    if (options.persist && options.modal) {
        // Determine if this form should "persist", or be dismissed?
        var chk = $(options.modal).find('#modal-persist');

        persist = chk.exists() && chk.prop('checked');
    }

    if (persist) {
        cache = false;
    }

    var msg_target = null;

    if (persist) {
        // If the modal is persistant, the target for any messages should be the modal!
        msg_target = $(options.modal).find('#pre-form-content');
    }

    // Display any messages
    if (response && (response.success || options.successMessage)) {
        showAlertOrCache(
            response.success || options.successMessage,
            cache,
            {
                style: 'success',
                target: msg_target,
            });
    }

    if (response && response.info) {
        showAlertOrCache(response.info, cache, {style: 'info'});
    }

    if (response && response.warning) {
        showAlertOrCache(response.warning, cache, {style: 'warning'});
    }

    if (response && response.danger) {
        showAlertOrCache(response.danger, cache, {style: 'danger'});
    }

    if (persist) {
        // Instead of closing the form and going somewhere else,
        // reload (empty) the form so the user can input more data

        // Reset the status of the "submit" button
        if (options.modal) {
            enableSubmitButton(options, true);
        }

        // Remove any error flags from the form
        clearFormErrors(options);

    } else {

        // Close the modal
        if (!options.preventClose) {
            // Note: The modal will be deleted automatically after closing
            $(options.modal).modal('hide');
        }

        if (options.onSuccess) {
            // Callback function
            options.onSuccess(response, options);
        }

        if (options.follow && response.url) {
            // Follow the returned URL
            window.location.href = response.url;
        } else if (options.reload) {
            // Reload the current page
            location.reload();
        } else if (options.redirect) {
            // Redirect to a specified URL
            window.location.href = options.redirect;
        }
    }
}



/*
 * Remove all error text items from the form
 */
function clearFormErrors(options={}) {

    if (options && options.modal) {
        // Remove the individual error messages
        $(options.modal).find('.form-error-message').remove();

        $(options.modal).find('.modal-content').removeClass('modal-error');

        // Remove the "has error" class
        $(options.modal).find('.form-field-error').removeClass('form-field-error');

        // Hide the 'non field errors'
        $(options.modal).find('#non-field-errors').html('');
    } else {
        $('.form-error-message').remove();
        $('.form-field-errors').removeClass('form-field-error');
        $('#non-field-errors').html('');
    }
}

/*
 * Display form error messages as returned from the server,
 * specifically for errors returned in an array.
 *
 * We need to know the unique ID of each item in the array,
 * and the array length must equal the length of the array returned from the server
 *
 * arguments:
 * - response: The JSON error response from the server
 * - parent: The name of the parent field e.g. "items"
 * - options: The global options struct
 *
 * options:
 * - nested: A map of nested ID values for the "parent" field
 *           e.g.
 *           {
 *               "items": [
 *                  1,
 *                  2,
 *                  12
 *               ]
 *           }
 *
 */

function handleNestedErrors(errors, field_name, options={}) {

    var error_list = errors[field_name];

    // Ignore null or empty list
    if (!error_list) {
        return;
    }

    var nest_list = nest_list = options['nested'][field_name];

    // Nest list must be provided!
    if (!nest_list) {
        console.warn(`handleNestedErrors missing nesting options for field '${fieldName}'`);
        return;
    }

    for (var idx = 0; idx < error_list.length; idx++) {

        var error_item = error_list[idx];

        if (idx >= nest_list.length) {
            console.warn(`handleNestedErrors returned greater number of errors (${error_list.length}) than could be handled (${nest_list.length})`);
            break;
        }

        // Extract the particular ID of the nested item
        var nest_id = nest_list[idx];

        // Here, error_item is a map of field names to error messages
        for (sub_field_name in error_item) {

            var errors = error_item[sub_field_name];

            if (sub_field_name == 'non_field_errors') {

                var row = null;

                if (options.modal) {
                    row = $(options.modal).find(`#items_${nest_id}`);
                } else {
                    row = $(`#items_${nest_id}`);
                }

                for (var ii = errors.length - 1; ii >= 0; ii--) {

                    var html = `
                    <div id='error_${ii}_non_field_error' class='help-block form-field-error form-error-message'>
                        <strong>${errors[ii]}</strong>
                    </div>`;

                    row.after(html);
                }

            }

            // Find the target (nested) field
            var target = `${field_name}_${sub_field_name}_${nest_id}`;

            for (var ii = errors.length-1; ii >= 0; ii--) {

                var error_text = errors[ii];

                addFieldErrorMessage(target, error_text, ii, options);
            }
        }
    }
}



/*
 * Display form error messages as returned from the server.
 *
 * arguments:
 * - errors: The JSON error response from the server
 * - fields: The form data object
 * - options: Form options provided by the client
 */
function handleFormErrors(errors, fields={}, options={}) {

    // Reset the status of the "submit" button
    if (options.modal) {
        enableSubmitButton(options, true);
    }

    // Remove any existing error messages from the form
    clearFormErrors(options);

    var non_field_errors = null;

    if (options.modal) {
        non_field_errors = $(options.modal).find('#non-field-errors');
    } else {
        non_field_errors = $('#non-field-errors');
    }

    // TODO: Display the JSON error text when hovering over the "info" icon
    non_field_errors.append(
        `<div class='alert alert-block alert-danger'>
            <b>{% trans "Form errors exist" %}</b>
            <span id='form-errors-info' class='float-right fas fa-info-circle icon-red'>
            </span>
        </div>`
    );

    // Non-field errors?
    if ('non_field_errors' in errors) {

        var nfe = errors.non_field_errors;

        for (var idx = 0; idx < nfe.length; idx++) {
            var err = nfe[idx];

            var html = `
            <div class='alert alert-block alert-danger'>
                ${err}
            </div>`;

            non_field_errors.append(html);
        }
    }

    var first_error_field = null;

    for (var field_name in errors) {

        var field = fields[field_name] || {};

        if ((field.type == 'field') && ('child' in field)) {
            // This is a "nested" field
            handleNestedErrors(errors, field_name, options);
        } else {
            // This is a "simple" field

            var field_errors = errors[field_name];

            if (field_errors && !first_error_field && isFieldVisible(field_name, options)) {
                first_error_field = field_name;
            }

            // Add an entry for each returned error message
            for (var ii = field_errors.length-1; ii >= 0; ii--) {

                var error_text = field_errors[ii];

                addFieldErrorMessage(field_name, error_text, ii, options);
            }
        }
    }

    if (first_error_field) {
        // Ensure that the field in question is visible
        document.querySelector(`#div_id_${field_name}`).scrollIntoView({
            behavior: 'smooth',
        });
    } else {
        // Scroll to the top of the form
        $(options.modal).find('.modal-form-content-wrapper').scrollTop(0);
    }

    $(options.modal).find('.modal-content').addClass('modal-error');
}


/*
 * Add a rendered error message to the provided field
 */
function addFieldErrorMessage(name, error_text, error_idx=0, options={}) {

    field_name = getFieldName(name, options);

    var field_dom = null;

    if (options && options.modal) {
        $(options.modal).find(`#div_id_${field_name}`).addClass('form-field-error');
        field_dom = $(options.modal).find(`#errors-${field_name}`);
    } else {
        $(`#div_id_${field_name}`).addClass('form-field-error');
        field_dom = $(`#errors-${field_name}`);
    }

    if (field_dom.exists()) {

        var error_html = `
        <span id='error_${error_idx}_id_${field_name}' class='help-block form-error-message'>
            <strong>${error_text}</strong>
        </span>`;

        field_dom.append(error_html);
    } else {
        console.warn(`addFieldErrorMessage could not locate field '${field_name}'`);
    }
}


function isFieldVisible(field, options) {

    return $(options.modal).find(`#div_id_${field}`).is(':visible');
}


/*
 * Attach callbacks to specified fields,
 * triggered after the field value is edited.
 *
 * Callback function is called with arguments (name, field, options)
 */
function addFieldCallbacks(fields, options) {

    for (var idx = 0; idx < options.field_names.length; idx++) {

        var name = options.field_names[idx];

        var field = fields[name];

        if (!field || !field.onEdit) continue;

        addFieldCallback(name, field, options);
    }
}


function addFieldCallback(name, field, options) {

    var el = getFormFieldElement(name, options);

    el.change(function() {

        var value = getFormFieldValue(name, field, options);

        field.onEdit(value, name, field, options);
    });
}


function addClearCallbacks(fields, options) {

    for (var idx = 0; idx < options.field_names.length; idx++) {

        var name = options.field_names[idx];

        var field = fields[name];

        if (!field || field.required) continue;

        addClearCallback(name, field, options);
    }
}


function addClearCallback(name, field, options={}) {

    var field_name = getFieldName(name, options);

    var el = null;

    if (options && options.modal) {
        el = $(options.modal).find(`#clear_${field_name}`);
    } else {
        el = $(`#clear_${field_name}`);
    }

    if (!el) {
        console.warn(`addClearCallback could not find field '${name}'`);
        return;
    }

    el.click(function() {
        updateFieldValue(name, null, field, options);
    });
}


// Initialize callbacks and initial states for groups
function initializeGroups(fields, options) {

    var modal = options.modal;

    // Callback for when the group is expanded
    $(modal).find('.form-panel-content').on('show.bs.collapse', function() {

        var panel = $(this).closest('.form-panel');
        var group = panel.attr('group');

        var icon = $(modal).find(`#group-icon-${group}`);

        icon.removeClass('fa-angle-right');
        icon.addClass('fa-angle-up');
    });

    // Callback for when the group is collapsed
    $(modal).find('.form-panel-content').on('hide.bs.collapse', function() {

        var panel = $(this).closest('.form-panel');
        var group = panel.attr('group');

        var icon = $(modal).find(`#group-icon-${group}`);

        icon.removeClass('fa-angle-up');
        icon.addClass('fa-angle-right');
    });

    // Set initial state of each specified group
    for (var group in options.groups) {

        var group_options = options.groups[group];

        if (group_options.collapsed) {
            $(modal).find(`#form-panel-content-${group}`).collapse('hide');
        } else {
            $(modal).find(`#form-panel-content-${group}`).collapse('show');
        }

        if (group_options.hidden) {
            hideFormGroup(group, options);
        }
    }
}

// Set the placeholder value for a field
function setFormInputPlaceholder(name, placeholder, options) {
    $(options.modal).find(`#id_${name}`).attr('placeholder', placeholder);
}

// Clear a form input
function clearFormInput(name, options) {
    updateFieldValue(name, null, {}, options);
}

// Disable a form input
function disableFormInput(name, options) {
    $(options.modal).find(`#id_${name}`).prop('disabled', true);
}


// Enable a form input
function enableFormInput(name, options) {
    $(options.modal).find(`#id_${name}`).prop('disabled', false);
}


// Hide a form input
function hideFormInput(name, options) {
    $(options.modal).find(`#div_id_${name}`).hide();
}


// Show a form input
function showFormInput(name, options) {
    $(options.modal).find(`#div_id_${name}`).show();
}


// Hide a form group
function hideFormGroup(group, options) {
    $(options.modal).find(`#form-panel-${group}`).hide();
}


// Show a form group
function showFormGroup(group, options) {
    $(options.modal).find(`#form-panel-${group}`).show();
}


function setFormGroupVisibility(group, vis, options) {
    if (vis) {
        showFormGroup(group, options);
    } else {
        hideFormGroup(group, options);
    }
}


function initializeRelatedFields(fields, options={}) {

    var field_names = options.field_names;

    for (var idx = 0; idx < field_names.length; idx++) {

        var name = field_names[idx];

        var field = fields[name] || null;

        if (!field || field.hidden) continue;

        switch (field.type) {
        case 'related field':
            initializeRelatedField(field, fields, options);
            break;
        case 'choice':
            initializeChoiceField(field, fields, options);
            break;
        default:
            break;
        }
    }
}


/*
 * Add a button to launch a secondary modal, to create a new modal instance.
 *
 * arguments:
 * - name: The name of the field
 * - field: The field data object
 * - options: The options object provided by the client
 */
function addSecondaryModal(field, fields, options) {

    var field_name = getFieldName(field.name, options);

    var depth = options.depth || 0;

    var html = `
    <span style='float: right;'>
        <div type='button' class='btn btn-primary btn-secondary btn-form-secondary' title='${field.secondary.title || field.secondary.label}' id='btn-new-${field_name}'>
            ${field.secondary.label || field.secondary.title}
        </div>
    </span>`;

    $(options.modal).find(`label[for="id_${field_name}"]`).append(html);

    // Callback function when the secondary button is pressed
    $(options.modal).find(`#btn-new-${field_name}`).click(function() {

        var secondary = field.secondary;

        // Determine the API query URL
        var url = secondary.api_url || field.api_url;

        // If the "fields" attribute is a function, call it with data
        if (secondary.fields instanceof Function || secondary.fieldsFunction instanceof Function) {

            // Extract form values at time of button press
            var data = extractFormData(fields, options);

            // Backup and execute fields function in sequential executions of modal
            if (secondary.fields instanceof Function) {
                secondary.fieldsFunction = secondary.fields;
            } else if (secondary.fieldsFunction instanceof Function) {
                secondary.fields = secondary.fieldsFunction;
            }

            secondary.fields = secondary.fields(data);
        }

        // If no onSuccess function is defined, provide a default one
        if (!secondary.onSuccess) {
            secondary.onSuccess = function(data) {

                // Force refresh from the API, to get full detail
                inventreeGet(`${url}${data.pk}/`, {}, {
                    success: function(responseData) {
                        setRelatedFieldData(field.name, responseData, options);
                    }
                });
            };
        }

        // Relinquish keyboard focus for this modal
        $(options.modal).modal({
            keyboard: false,
        });

        // Method should be "POST" for creation
        secondary.method = secondary.method || 'POST';

        secondary.modal = null;

        secondary.depth = depth + 1;

        constructForm(
            url,
            secondary
        );
    });
}


/*
 * Initialize a single related-field
 *
 * argument:
 * - modal: DOM identifier for the modal window
 * - name: name of the field e.g. 'location'
 * - field: Field definition from the OPTIONS request
 * - options: Original options object provided by the client
 */
function initializeRelatedField(field, fields, options={}) {

    var name = field.name;

    if (!field.api_url) {
        console.warn(`Related field '${name}' missing 'api_url' parameter.`);
        return;
    }

    // Find the select element and attach a select2 to it
    var select = getFormFieldElement(name, options);

    // Add a button to launch a 'secondary' modal
    if (field.secondary != null) {
        addSecondaryModal(field, fields, options);
    }

    // TODO: Add 'placeholder' support for entry select2 fields

    // limit size for AJAX requests
    var pageSize = options.pageSize || 25;

    var parent = null;
    var auto_width = false;
    var width = '100%';

    // Special considerations if the select2 input is a child of a modal
    if (options && options.modal) {
        parent = $(options.modal);
        auto_width = true;
        width = null;
    }

    select.select2({
        placeholder: '',
        dropdownParent: parent,
        dropdownAutoWidth: auto_width,
        width: width,
        language: {
            noResults: function(query) {
                if (field.noResults) {
                    return field.noResults(query);
                } else {
                    return '{% trans "No results found" %}';
                }
            }
        },
        ajax: {
            url: field.api_url,
            dataType: 'json',
            delay: 250,
            cache: true,
            data: function(params) {

                var offset = 0;

                if (!params.page) {
                    offset = 0;
                } else {
                    offset = (params.page - 1) * pageSize;
                }

                // Custom query filters can be specified against each field
                var query = field.filters || {};

                // Add search and pagination options
                query.search = params.term;
                query.offset = offset;
                query.limit = pageSize;

                // Allow custom run-time filter augmentation
                if ('adjustFilters' in field) {
                    query = field.adjustFilters(query, options);
                }

                return query;
            },
            processResults: function(response) {
                // Convert the returned InvenTree data into select2-friendly format

                var data = [];

                var more = false;

                if ('count' in response && 'results' in response) {
                    // Response is paginated
                    data = response.results;

                    // Any more data available?
                    if (response.next) {
                        more = true;
                    }

                } else {
                    // Non-paginated response
                    data = response;
                }

                // Each 'row' must have the 'id' attribute
                for (var idx = 0; idx < data.length; idx++) {
                    data[idx].id = data[idx].pk;
                }

                // Ref: https://select2.org/data-sources/formats
                var results = {
                    results: data,
                    pagination: {
                        more: more,
                    }
                };

                return results;
            },
        },
        templateResult: function(item) {

            // Extract 'instance' data passed through from an initial value
            // Or, use the raw 'item' data as a backup
            var data = item;

            if (item.element && item.element.instance) {
                data = item.element.instance;
            }

            if (!data.pk) {
                return $(searching());
            }

            // Custom formatting for the search results
            if (field.model) {
                // If the 'model' is specified, hand it off to the custom model render
                var html = renderModelData(name, field.model, data, field, options);
                return $(html);
            } else {
                // Return a simple renderering
                console.warn(`templateResult() missing 'field.model' for '${name}'`);
                return `${name} - ${item.id}`;
            }
        },
        templateSelection: function(item) {

            // Extract 'instance' data passed through from an initial value
            // Or, use the raw 'item' data as a backup
            var data = item;

            if (item.element && item.element.instance) {
                data = item.element.instance;
            }

            // Run optional callback function
            if (field.onSelect && data) {
                field.onSelect(data, field, options);
            }

            if (!data.pk) {
                return field.placeholder || '';
            }

            // Custom formatting for selected item
            if (field.model) {
                // If the 'model' is specified, hand it off to the custom model render
                var html = renderModelData(name, field.model, data, field, options);
                return $(html);
            } else {
                // Return a simple renderering
                console.warn(`templateSelection() missing 'field.model' for '${name}'`);
                return `${name} - ${item.id}`;
            }
        }
    });

    // If a 'value' is already defined, grab the model info from the server
    if (field.value) {

        var pk = field.value;
        var url = `${field.api_url}/${pk}/`.replace('//', '/');

        inventreeGet(url, field.filters || {}, {
            success: function(data) {
                setRelatedFieldData(name, data, options);
            }
        });
    } else if (field.auto_fill) {
        // Attempt to auto-fill the field

        var filters = {};

        // Update with nominal field fields
        Object.assign(filters, field.filters || {});

        // Update with filters only used for initial filtering
        Object.assign(filters, field.auto_fill_filters || {});

        // Enforce pagination, limit to a single return (for fast query)
        filters.limit = 1;
        filters.offset = 0;

        inventreeGet(field.api_url, filters || {}, {
            success: function(data) {

                // Only a single result is available, given the provided filters
                if (data.count == 1) {
                    setRelatedFieldData(name, data.results[0], options);

                    // Run "callback" function (if supplied)
                    if (field.onEdit) {
                        field.onEdit(data.results[0], name, field, options);
                    }
                }
            }
        });
    }
}


/*
 * Set the value of a select2 instace for a "related field",
 * e.g. with data returned from a secondary modal
 *
 * arguments:
 * - name: The name of the field
 * - data: JSON data representing the model instance
 * - options: The modal form specifications
 */
function setRelatedFieldData(name, data, options={}) {

    var select = getFormFieldElement(name, options);

    var option = new Option(name, data.pk, true, true);

    // Assign the JSON data to the 'instance' attribute,
    // so we can access and render it later
    option.instance = data;

    select.append(option).trigger('change');

    select.trigger({
        type: 'select2:select',
        params: {
            data: data
        }
    });
}


function initializeChoiceField(field, fields, options) {

    var select = getFormFieldElement(field.name, options);

    select.select2({
        dropdownAutoWidth: false,
        dropdownParent: $(options.modal),
    });
}


// Render a 'no results' element
function searching() {
    return `<span>{% trans "Searching" %}...</span>`;
}

/*
 * Render a "foreign key" model reference in a select2 instance.
 * Allows custom rendering with access to the entire serialized object.
 *
 * arguments:
 * - name: The name of the field e.g. 'location'
 * - model: The name of the InvenTree model e.g. 'stockitem'
 * - data: The JSON data representation of the modal instance (GET request)
 * - parameters: The field definition (OPTIONS) request
 * - options: Other options provided at time of modal creation by the client
 */
function renderModelData(name, model, data, parameters, options) {

    if (!data) {
        return parameters.placeholder || '';
    }

    // TODO: Implement this function for various models

    var html = null;

    var renderer = null;

    // Find a custom renderer
    switch (model) {
    case 'company':
        renderer = renderCompany;
        break;
    case 'stockitem':
        renderer = renderStockItem;
        break;
    case 'stocklocation':
        renderer = renderStockLocation;
        break;
    case 'part':
        renderer = renderPart;
        break;
    case 'partcategory':
        renderer = renderPartCategory;
        break;
    case 'partparametertemplate':
        renderer = renderPartParameterTemplate;
        break;
    case 'purchaseorder':
        renderer = renderPurchaseOrder;
        break;
    case 'salesorder':
        renderer = renderSalesOrder;
        break;
    case 'salesordershipment':
        renderer = renderSalesOrderShipment;
        break;
    case 'manufacturerpart':
        renderer = renderManufacturerPart;
        break;
    case 'supplierpart':
        renderer = renderSupplierPart;
        break;
    case 'build':
        renderer = renderBuild;
        break;
    case 'owner':
        renderer = renderOwner;
        break;
    case 'user':
        renderer = renderUser;
        break;
    default:
        break;
    }

    if (renderer != null) {
        html = renderer(name, data, parameters, options);
    }

    if (html != null) {
        return html;
    } else {
        console.error(`Rendering not implemented for model '${model}'`);
        // Simple text rendering
        return `${model} - ID ${data.id}`;
    }
}


/*
 * Construct a field name for the given field
 */
function getFieldName(name, options={}) {
    var field_name = name;

    if (options.field_suffix) {
        field_name += options.field_suffix;
    }

    if (options && options.depth) {
        field_name += `_${options.depth}`;
    }

    return field_name;
}


/*
 * Construct a single form 'field' for rendering in a form.
 *
 * arguments:
 * - name: The 'name' of the field
 * - parameters: The field parameters supplied by the DRF OPTIONS method
 *
 * options:
 * -
 *
 * The function constructs a fieldset which mostly replicates django "crispy" forms:
 *
 * - Field name
 * - Field <input> (depends on specified field type)
 * - Field description (help text)
 * - Field errors
 */
function constructField(name, parameters, options={}) {

    var html = '';

    // Shortcut for simple visual fields
    if (parameters.type == 'candy') {
        return constructCandyInput(name, parameters, options);
    }

    var field_name = getFieldName(name, options);

    // Hidden inputs are rendered without label / help text / etc
    if (parameters.hidden) {
        return constructHiddenInput(field_name, parameters, options);
    }

    // Are we ending a group?
    if (options.current_group && parameters.group != options.current_group) {
        html += `</div></div>`;

        // Null out the current "group" so we can start a new one
        options.current_group = null;
    }

    // Are we starting a new group?
    if (parameters.group) {

        var group = parameters.group;

        var group_id = getFieldName(group, options);

        var group_options = options.groups[group] || {};

        // Are we starting a new group?
        // Add HTML for the start of a separate panel
        if (parameters.group != options.current_group) {

            html += `
            <div class='panel form-panel' id='form-panel-${group_id}' group='${group}'>
                <div class='panel-heading form-panel-heading' id='form-panel-heading-${group_id}'>`;
            if (group_options.collapsible) {
                html += `
                <div data-bs-toggle='collapse' data-bs-target='#form-panel-content-${group_id}'>
                    <a href='#'><span id='group-icon-${group_id}' class='fas fa-angle-up'></span>
                `;
            } else {
                html += `<div>`;
            }

            html += `<h4 style='display: inline;'>${group_options.title || group}</h4>`;

            if (group_options.collapsible) {
                html += `</a>`;
            }

            html += `
                </div></div>
                <div class='panel-content form-panel-content' id='form-panel-content-${group_id}'>
            `;
        }

        // Keep track of the group we are in
        options.current_group = group;
    }

    var form_classes = options.form_classes || 'form-group';

    if (parameters.errors) {
        form_classes += ' form-field-error';
    }

    // Optional content to render before the field
    if (parameters.before) {
        html += parameters.before;
    }

    var hover_title = '';

    if (parameters.help_text) {
        hover_title = ` title='${parameters.help_text}'`;
    }

    html += `<div id='div_id_${field_name}' class='${form_classes}' ${hover_title}>`;

    // Add a label
    if (!options.hideLabels) {
        html += constructLabel(name, parameters);
    }

    html += `<div class='controls'>`;

    // Does this input deserve "extra" decorators?
    var extra = (parameters.icon != null) || (parameters.prefix != null) || (parameters.prefixRaw != null);

    // Some fields can have 'clear' inputs associated with them
    if (!parameters.required && !parameters.read_only) {
        switch (parameters.type) {
        case 'string':
        case 'url':
        case 'email':
        case 'integer':
        case 'float':
        case 'decimal':
        case 'related field':
        case 'date':
            extra = true;
            break;
        default:
            break;
        }
    }

    if (extra) {
        html += `<div class='input-group'>`;

        if (parameters.prefix) {
            html += `<span class='input-group-text'>${parameters.prefix}</span>`;
        } else if (parameters.prefixRaw) {
            html += parameters.prefixRaw;
        } else if (parameters.icon) {
            html += `<span class='input-group-text'><span class='fas ${parameters.icon}'></span></span>`;
        }
    }

    html += constructInput(field_name, parameters, options);

    if (extra) {

        if (!parameters.required && !options.hideClearButton) {
            html += `
            <span class='input-group-text form-clear' id='clear_${field_name}' title='{% trans "Clear input" %}'>
                <span class='icon-red fas fa-backspace'></span>
            </span>`;
        }

        html += `</div>`; // input-group
    }

    if (parameters.help_text && !options.hideLabels) {

        // Boolean values are handled differently!
        if (parameters.type != 'boolean' && !parameters.hidden) {
            html += constructHelpText(name, parameters, options);
        }
    }

    // Div for error messages
    html += `<div id='errors-${field_name}'></div>`;

    html += `</div>`; // controls
    html += `</div>`; // form-group

    if (parameters.after) {
        html += parameters.after;
    }

    return html;
}


/*
 * Construct a 'label' div
 *
 * arguments:
 * - name: The name of the field
 * - required: Is this a required field?
 */
function constructLabel(name, parameters) {

    var label_classes = 'control-label';

    if (parameters.required) {
        label_classes += ' requiredField';
    }

    var html = `<label class='${label_classes}' for='id_${name}'>`;

    if (parameters.label) {
        html += `${parameters.label}`;
    } else {
        html += `${name}`;
    }

    if (parameters.required) {
        html += `<span class='asteriskField'>*</span>`;
    }

    html += `</label>`;

    return html;
}


/*
 * Construct a form input based on the field parameters
 *
 * arguments:
 * - name: The name of the field
 * - parameters: Field parameters returned by the OPTIONS method
 *
 */
function constructInput(name, parameters, options={}) {

    var html = '';

    var func = null;

    switch (parameters.type) {
    case 'boolean':
        func = constructCheckboxInput;
        break;
    case 'string':
    case 'url':
    case 'email':
        func = constructTextInput;
        break;
    case 'integer':
    case 'float':
    case 'decimal':
        func = constructNumberInput;
        break;
    case 'choice':
        func = constructChoiceInput;
        break;
    case 'related field':
        func = constructRelatedFieldInput;
        break;
    case 'image upload':
    case 'file upload':
        func = constructFileUploadInput;
        break;
    case 'date':
        func = constructDateInput;
        break;
    case 'candy':
        func = constructCandyInput;
        break;
    case 'raw':
        func = constructRawInput;
    default:
        // Unsupported field type!
        break;
    }

    if (func != null) {
        html = func(name, parameters, options);
    } else {
        console.warn(`Unhandled form field type: '${parameters.type}'`);
    }

    return html;
}


// Construct a set of default input options which apply to all input types
function constructInputOptions(name, classes, type, parameters, options={}) {

    var opts = [];

    opts.push(`id='id_${name}'`);

    opts.push(`class='${classes}'`);

    opts.push(`name='${name}'`);

    opts.push(`type='${type}'`);

    if (parameters.title || parameters.help_text) {
        opts.push(`title='${parameters.title || parameters.help_text}'`);
    }

    // Read only?
    if (parameters.read_only) {
        opts.push(`readonly=''`);
    }

    if (parameters.value != null) {
        if (parameters.type == 'boolean') {
            // Special consideration of a boolean (checkbox) value
            if (parameters.value == true || parameters.value.toString().toLowerCase() == 'true') {
                opts.push('checked');
            }
        } else {
            // Existing value?
            opts.push(`value='${parameters.value}'`);
        }
    } else if (parameters.default != null) {
        // Otherwise, a defualt value?
        opts.push(`value='${parameters.default}'`);
    }

    // Maximum input length
    if (parameters.max_length != null) {
        opts.push(`maxlength='${parameters.max_length}'`);
    }

    // Minimum input length
    if (parameters.min_length != null) {
        opts.push(`minlength='${parameters.min_length}'`);
    }

    // Maximum value
    if (parameters.max_value != null) {
        opts.push(`max='${parameters.max_value}'`);
    }

    // Minimum value
    if (parameters.min_value != null) {
        opts.push(`min='${parameters.min_value}'`);
    }

    // Field is required?
    if (parameters.required) {
        opts.push(`required=''`);
    }

    // Placeholder?
    if (parameters.placeholder != null) {
        opts.push(`placeholder='${parameters.placeholder}'`);
    }

    switch (parameters.type) {
    case 'boolean':
        break;
    case 'integer':
    case 'float':
    case 'decimal':
        opts.push(`step='any'`);
        break;
    default:
        break;
    }

    if (parameters.multiline) {
        return `<textarea ${opts.join(' ')}></textarea>`;
    } else if (parameters.type == 'boolean') {

        if (parameters.hidden) {
            return '';
        }

        var help_text = '';

        if (!options.hideLabels && parameters.help_text) {
            help_text = `<em><small>${parameters.help_text}</small></em>`;
        }

        return `
        <div class='form-check form-switch'>
            <input ${opts.join(' ')}>
            <label class='form-check-label' for=''>
                ${help_text}
            </label>
        </div>
        `;
    } else {
        return `<input ${opts.join(' ')}>`;
    }
}


// Construct a "hidden" input
function constructHiddenInput(name, parameters, options={}) {

    return constructInputOptions(
        name,
        'hiddeninput',
        'hidden',
        parameters,
        options
    );
}


// Construct a "checkbox" input
function constructCheckboxInput(name, parameters, options={}) {

    return constructInputOptions(
        name,
        'form-check-input',
        'checkbox',
        parameters,
        options
    );
}


// Construct a "text" input
function constructTextInput(name, parameters) {

    var classes = '';
    var type = '';

    switch (parameters.type) {
    default:
        classes = 'textinput textInput form-control';
        type = 'text';
        break;
    case 'url':
        classes = 'urlinput form-control';
        type = 'url';
        break;
    case 'email':
        classes = 'emailinput form-control';
        type = 'email';
        break;
    }

    return constructInputOptions(
        name,
        classes,
        type,
        parameters
    );
}


// Construct a "number" field
function constructNumberInput(name, parameters) {

    return constructInputOptions(
        name,
        'numberinput form-control',
        'number',
        parameters
    );
}


// Construct a "choice" input
function constructChoiceInput(name, parameters) {

    var html = `<select id='id_${name}' class='select form-control' name='${name}'>`;

    var choices = parameters.choices || [];

    for (var idx = 0; idx < choices.length; idx++) {

        var choice = choices[idx];

        var selected = '';

        if (parameters.value && parameters.value == choice.value) {
            selected = ` selected=''`;
        }

        html += `<option value='${choice.value}'${selected}>`;
        html += `${choice.display_name}`;
        html += `</option>`;
    }

    html += `</select>`;

    return html;
}


/*
 * Construct a "related field" input.
 * This will create a "select" input which will then, (after form is loaded),
 * be converted into a select2 input.
 * This will then be served custom data from the API (as required)...
 */
function constructRelatedFieldInput(name) {

    var html = `<select id='id_${name}' class='select form-control' name='${name}'></select>`;

    // Don't load any options - they will be filled via an AJAX request

    return html;
}


/*
 * Construct a field for file upload
 */
function constructFileUploadInput(name, parameters) {

    var cls = 'clearablefileinput';

    if (parameters.required) {
        cls = 'fileinput';
    }

    return constructInputOptions(
        name,
        cls,
        'file',
        parameters
    );
}


/*
 * Construct a field for a date input
 */
function constructDateInput(name, parameters) {

    return constructInputOptions(
        name,
        'dateinput form-control',
        'date',
        parameters
    );
}


/*
 * Construct a "candy" field input
 * No actual field data!
 */
function constructCandyInput(name, parameters) {

    return parameters.html;

}


/*
 * Construct a "raw" field input
 * No actual field data!
 */
function constructRawInput(name, parameters) {

    return parameters.html;

}


/*
 * Construct a 'help text' div based on the field parameters
 *
 * arguments:
 * - name: The name of the field
 * - parameters: Field parameters returned by the OPTIONS method
 *
 */
function constructHelpText(name, parameters) {

    var html = `<div id='hint_id_${name}' class='help-block'><i>${parameters.help_text}</i></div>`;

    return html;
}


/*
 * Construct a dialog to select import fields
 */
function selectImportFields(url, data={}, options={}) {

    if (!data.model_fields) {
        console.warn(`selectImportFields is missing 'model_fields'`);
        return;
    }

    if (!data.file_fields) {
        console.warn(`selectImportFields is missing 'file_fields'`);
        return;
    }

    var choices = [];

    // Add an "empty" value
    choices.push({
        value: '',
        display_name: '-----',
    });

    for (const [name, field] of Object.entries(data.model_fields)) {
        choices.push({
            value: name,
            display_name: field.label || name,
        });
    }

    var rows = '';

    var field_names = Object.keys(data.file_fields);

    for (var idx = 0; idx < field_names.length; idx++) {

        var field_name = field_names[idx];

        var choice_input = constructInput(
            `column_${idx}`,
            {
                type: 'choice',
                label: field_name,
                value: data.file_fields[field_name].value,
                choices: choices,
            }
        );

        rows += `<tr><td><em>${field_name}</em></td><td>${choice_input}</td></tr>`;
    }

    var headers = `<tr><th>{% trans "File Column" %}</th><th>{% trans "Field Name" %}</th></tr>`;

    var html = '';

    if (options.preamble) {
        html += options.preamble;
    }

    html += `<table class='table table-condensed'>${headers}${rows}</table>`;

    constructForm(url, {
        method: 'POST',
        title: '{% trans "Select Columns" %}',
        fields: {},
        preFormContent: html,
        onSubmit: function(fields, opts) {

            var columns = [];

            for (var idx = 0; idx < field_names.length; idx++) {
                columns.push(getFormFieldValue(`column_${idx}`, {}, opts));
            }

            showModalSpinner(opts.modal);

            inventreePut(
                opts.url,
                {
                    columns: columns,
                    rows: data.rows,
                },
                {
                    method: 'POST',
                    success: function(response) {
                        handleFormSuccess(response, opts);

                        if (options.success) {
                            options.success(response);
                        }
                    },
                    error: function(xhr) {

                        $(opts.modal).find('#modal-progress-spinner').hide();

                        switch (xhr.status) {
                        case 400:
                            handleFormErrors(xhr.responseJSON, fields, opts);
                            break;
                        default:
                            $(opts.modal).modal('hide');

                            console.error(`upload error at ${opts.url}`);
                            showApiError(xhr, opts.url);
                            break;
                        }
                    }
                }
            );
        },
    });
}
