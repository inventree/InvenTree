{% load i18n %}
{% load inventree_extras %}

/**
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
 */

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
function getApiEndpointOptions(url, callback, options) {

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
        error: function(request, status, error) {
            // TODO: Handle error
            console.log(`ERROR in getApiEndpointOptions at '${url}'`);
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

        if (field.default != null) {
            field.value = field.default;
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
        type: 'GET',
        contentType: 'application/json',
        dataType: 'json',
        accepts: {
            json: 'application/json',
        },
        success: function(data) {

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
        error: function(request, status, error) {
            // TODO: Handle error here
            console.log(`ERROR in constructChangeForm at '${url}'`);
        }
    })

}


/*
 * Request API OPTIONS data from the server,
 * and construct a modal form based on the response.
 * 
 * options:
 * - method: The HTTP method e.g. 'PUT', 'POST', 'DELETE',
 * - title: The form title
 * - fields: list of fields to display
 * - exclude: List of fields to exclude
 */
function constructForm(url, options) {

    // Save the URL 
    options.url = url;

    // Default HTTP method
    options.method = options.method || 'PATCH';

    // Request OPTIONS endpoint from the API
    getApiEndpointOptions(url, function(OPTIONS) {

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
                    console.log('cannot POST');
                    // TODO
                }
                break;
            case 'PUT':
            case 'PATCH':
                if (canChange(OPTIONS)) {
                    constructChangeForm(OPTIONS.actions.PUT, options);
                } else {
                    // User does not have permission to PUT/PATCH to the endpoint
                    // TODO
                    console.log('cannot edit');
                }
                break;
            case 'DELETE':
                if (canDelete(OPTIONS)) {
                    console.log('delete');
                } else {
                    // User does not have permission to DELETE to the endpoint
                    // TODO
                    console.log('cannot delete');
                }
                break;
            case 'GET':
                if (canView(OPTIONS)) {
                    console.log('view');
                } else {
                    // User does not have permission to GET to the endpoint
                    // TODO
                    console.log('cannot view');
                }
                break;
            default:
                console.log(`constructForm() called with invalid method '${options.method}'`);
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

    // Provide each field object with its own name
    for(field in fields) {
        fields[field].name = field;

        var field_options = displayed_fields[field];

        // Copy custom options across to the fields object
        if (field_options) {

            // Override existing query filters (if provided!)
            fields[field].filters = Object.assign(fields[field].filters || {}, field_options.filters);

            // Secondary modal options
            fields[field].secondary = field_options.secondary;

            // Edit callback
            fields[field].onEdit = field_options.onEdit;

            // Field prefix
            fields[field].prefix = field_options.prefix;
        }
    }

    // Construct an ordered list of field names
    var field_names = [];

    for (var name in displayed_fields) {

        // Only push names which are actually in the set of fields
        if (name in fields) {
            field_names.push(name);
        } else {
            console.log(`WARNING: '${name}' does not match a valid field name.`);
        }
    }

    // Push the ordered field names into the options,
    // allowing successive functions to access them.
    options.field_names = field_names;

    // Render selected fields

    for (var idx = 0; idx < field_names.length; idx++) {

        var name = field_names[idx];

        var field = fields[name];

        switch (field.type) {
            // Skip field types which are simply not supported
            case 'nested object':
                continue;
            default:
                break;
        }

        var f = constructField(name, field, options);
        
        html += f;
    }

    // TODO: Dynamically create the modals,
    //       so that we can have an infinite number of stacks!

    options.modal = options.modal || '#modal-form';
    
    var modal = options.modal;

    modalEnable(modal, true);

    // Set the form title and button labels
    modalSetTitle(modal, options.title || '{% trans "Form Title" %}');
    modalSetSubmitText(options.submitText || '{% trans "Submit" %}');
    modalSetCloseText(options.cancelText || '{% trans "Cancel" %}');

    // Insert generated form content
    $(modal).find('.modal-form-content').html(html);
    
    $(modal).modal('show');

    updateFieldValues(fields, options);

    // Setup related fields
    initializeRelatedFields(fields, options);

    // Attach edit callbacks (if required)
    addFieldCallbacks(fields, options);

    attachToggle(modal);

    $(modal + ' .select2-container').addClass('select-full-width');
    $(modal + ' .select2-container').css('width', '100%');

    modalShowSubmitButton(modal, true);

    $(modal).off('click', '#modal-form-submit');
    $(modal).on('click', '#modal-form-submit', function() {

        submitFormData(fields, options);
    });
}


/*
 * Submit form data to the server.
 * 
 */
function submitFormData(fields, options) {

    // Data to be sent to the server
    var data = {};

    // Extract values for each field
    options.field_names.forEach(function(name) {

        var field = fields[name] || null;

        if (field) {

            var value = getFormFieldValue(name, field, options);

            data[name] = value;
        } else {
            console.log(`WARNING: Could not find field matching '${name}'`);
        }
    });

    // Submit data
    inventreePut(
        options.url,
        data,
        {
            method: options.method,
            success: function(response, status) {
                handleFormSuccess(response, options);
            },
            error: function(xhr, status, thrownError) {
                
                switch (xhr.status) {
                    case 400:  // Bad request
                        handleFormErrors(xhr.responseJSON, fields, options);
                        break;
                    default:
                        console.log(`WARNING: Unhandled response code - ${xhr.status}`);
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

        if (field == null) { continue; }

        var value = field.value;

        if (value == null) {
            value = field.default;
        }

        if (value == null) { continue; }

        var el = $(options.modal).find(`#id_${name}`);

        switch (field.type) {
            case 'boolean':
                el.prop('checked', value);
                break;
            case 'related field':
                // TODO?
                break;
            default:
                el.val(value);
                break;
        }
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
function getFormFieldValue(name, field, options) {

    // Find the HTML element
    var el = $(options.modal).find(`#id_${name}`);

    switch (field.type) {
        case 'boolean':
            return el.is(":checked");
        default:
            return el.val();
    }
}


/*
 * Handle successful form posting
 * 
 * arguments:
 * - response: The JSON response object from the server
 * - options: The original options object provided by the client
 */
function handleFormSuccess(response, options) {

    // Close the modal
    if (!options.preventClose) {
        // TODO: Actually just *delete* the modal,
        // rather than hiding it!!
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



/*
 * Remove all error text items from the form
 */
function clearFormErrors(options) {

    // Remove the individual error messages
    $(options.modal).find('.form-error-message').remove();

    // Remove the "has error" class
    $(options.modal).find('.has-error').removeClass('has-error');
}


/*
 * Display form error messages as returned from the server.
 * 
 * arguments:
 * - errors: The JSON error response from the server
 * - fields: The form data object
 * - options: Form options provided by the client
 */
function handleFormErrors(errors, fields, options) {

    // Remove any existing error messages from the form
    clearFormErrors(options);

    for (field_name in errors) {
        if (field_name in fields) {

            // Add the 'has-error' class
            $(options.modal).find(`#div_id_${field_name}`).addClass('has-error');

            var field_dom = $(options.modal).find(`#id_${field_name}`);

            var field_errors = errors[field_name];

            // Add an entry for each returned error message
            for (var idx = field_errors.length-1; idx >= 0; idx--) {

                var error_text = field_errors[idx];

                var html = `
                <span id='error_${idx+1}_id_${field_name}' class='help-block form-error-message'>
                    <strong>${error_text}</strong>
                </span>`;

                $(html).insertAfter(field_dom);
            }

        } else {
            console.log(`WARNING: handleFormErrors found no match for field '${field_name}'`);
        }
    }

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

    $(options.modal).find(`#id_${name}`).change(function() {
        field.onEdit(name, field, options);
    });
}


function initializeRelatedFields(fields, options) {

    var field_names = options.field_names;

    for (var idx = 0; idx < field_names.length; idx++) {

        var name = field_names[idx];

        var field = fields[name] || null;

        if (!field || field.type != 'related field') continue;

        if (!field.api_url) {
            // TODO: Provide manual api_url option?
            console.log(`Related field '${name}' missing 'api_url' parameter.`);
            continue;
        }

        initializeRelatedField(name, field, options);
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
function addSecondaryModal(name, field, options) {

    var html = `
    <span style='float: right;'>
        <div type='button' class='btn btn-primary btn-secondary' title='${field.secondary.title || field.secondary.label}' id='btn-new-${name}'>
            ${field.secondary.label}
        </div>
    </span>`;

    $(options.modal).find(`label[for="id_${name}"]`).append(html);

    // TODO: Launch a callback
}


/*
 * Initializea single related-field
 * 
 * argument:
 * - modal: DOM identifier for the modal window
 * - name: name of the field e.g. 'location'
 * - field: Field definition from the OPTIONS request
 * - options: Original options object provided by the client
 */
function initializeRelatedField(name, field, options) {

    // Find the select element and attach a select2 to it
    var select = $(options.modal).find(`#id_${name}`);

    // Add a button to launch a 'secondary' modal
    if (field.secondary != null) {
        addSecondaryModal(name, field, options);
    }

    // TODO: Add 'placeholder' support for entry select2 fields

    // limit size for AJAX requests
    var pageSize = options.pageSize || 25;

    select.select2({
        ajax: {
            url: field.api_url,
            dataType: 'json',
            allowClear: !field.required,
            dropdownParent: $(options.modal),
            dropdownAutoWidth: false,
            delay: 250,
            cache: true,
            data: function(params) {

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
        templateResult: function(item, container) {

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
                console.log(`WARNING: templateResult() missing 'field.model' for '${name}'`);
                return `${name} - ${item.id}`;
            }
        },
        templateSelection: function(item, container) {

            // Extract 'instance' data passed through from an initial value
            // Or, use the raw 'item' data as a backup
            var data = item;
            
            if (item.element && item.element.instance) {
                data = item.element.instance;
            }

            if (!data.pk) {
                return $(searching());
            }

            // Custom formatting for selected item
            if (field.model) {
                // If the 'model' is specified, hand it off to the custom model render
                var html = renderModelData(name, field.model, data, field, options);
                return $(html);
            } else {
                // Return a simple renderering
                console.log(`WARNING: templateSelection() missing 'field.model' for '${name}'`);
                return `${name} - ${item.id}`;
            }
        }
    });

    // If a 'value' is already defined, grab the model info from the server
    if (field.value) {
        var pk = field.value;
        var url = `${field.api_url}/${pk}/`.replace('//', '/');

        inventreeGet(url, {}, {
            success: function(data) {

                // Create a new option, simply use the model name as the text (for now)
                // Note: The correct rendering will be computed later by templateSelection function
                var option = new Option(name, data.pk, true, true);

                // Store the returned data as 'instance' parameter of the created option,
                // so that it can be retrieved later!
                option.instance = data;

                select.append(option).trigger('change');

                // manually trigger the `select2:select` event
                select.trigger({
                    type: 'select2:select',
                    params: {
                        data: data
                    }
                });
            }
        });
    }
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
        return '{% trans "Searching" %}...';
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
        default:
            break;
    }
    
    if (renderer != null) {
        html = renderer(name, data, parameters, options);
    }

    if (html != null) {
        return html;
    } else {
        console.log(`ERROR: Rendering not implemented for model '${model}'`);
        // Simple text rendering
        return `${model} - ID ${data.id}`;
    }
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
function constructField(name, parameters, options) {

    var field_name = `id_${name}`;

    var form_classes = 'form-group';

    if (parameters.errors) {
        form_classes += ' has-error';
    }

    var html = `<div id='div_${field_name}' class='${form_classes}'>`;

    // Add a label
    html += constructLabel(name, parameters);

    html += `<div class='controls'>`;
    
    if (parameters.prefix) {
        html += `<div class='input-group'><span class='input-group-addon'>${parameters.prefix}</span>`;
    }

    html += constructInput(name, parameters, options);

    if (parameters.prefix) {
        html += `</div>`;   // input-group
    }

    if (parameters.help_text) {
        html += constructHelpText(name, parameters, options);
    }

    html += `</div>`;   // controls
    html += `</div>`;   // form-group
    
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
function constructInput(name, parameters, options) {

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
        default:
            // Unsupported field type!
            break;
        }
        
    if (func != null) {
        html = func(name, parameters, options);
    } else {
        console.log(`WARNING: Unhandled form field type: '${parameters.type}'`);
    }

    return html;
}


// Construct a set of default input options which apply to all input types
function constructInputOptions(name, classes, type, parameters) {

    var opts = [];

    opts.push(`id='id_${name}'`);

    opts.push(`class='${classes}'`);

    opts.push(`name='${name}'`);

    opts.push(`type='${type}'`);

    // Read only?
    if (parameters.read_only) {
        opts.push(`readonly=''`);
    }

    if (parameters.value) {
        // Existing value?
        opts.push(`value='${parameters.value}'`);
    } else if (parameters.default) {
        // Otherwise, a defualt value?
        opts.push(`value='${parameters.default}'`);
    }

    // Maximum input length
    if (parameters.max_length) {
        opts.push(`maxlength='${parameters.max_length}'`);
    }

    // Minimum input length
    if (parameters.min_length) {
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
    if (parameters.placeholder) {
        opts.push(`placeholder='${parameters.placeholder}'`);
    }

    return `<input ${opts.join(' ')}>`;
}


// Construct a "checkbox" input
function constructCheckboxInput(name, parameters, options) {

    return constructInputOptions(
        name,
        'checkboxinput',
        'checkbox',
        parameters
    );

}


// Construct a "text" input
function constructTextInput(name, parameters, options) {

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
function constructNumberInput(name, parameters, options) {

    return constructInputOptions(
        name,
        'numberinput form-control',
        'number',
        parameters
    );
}


// Construct a "choice" input
function constructChoiceInput(name, parameters, options) {

    var html = `<select id='id_${name}' class='select form-control' name='${name}'>`;

    var choices = parameters.choices || [];

    // TODO: Select the selected value!

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
function constructRelatedFieldInput(name, parameters, options) {

    var html = `<select id='id_${name}' class='select form-control' name='${name}'></select>`;

    // Don't load any options - they will be filled via an AJAX request

    return html;
}


/*
 * Construct a 'help text' div based on the field parameters
 * 
 * arguments:
 * - name: The name of the field
 * - parameters: Field parameters returned by the OPTIONS method
 *  
 */
function constructHelpText(name, parameters, options) {
    
    var html = `<div id='hint_id_${name}' class='help-block'><i>${parameters.help_text}</i></div>`;

    return html;
}