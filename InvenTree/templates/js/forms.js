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
function getApiEndpointOptions(url, callback, options={}) {

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
 * Request API OPTIONS data from the server,
 * and construct a modal form based on the response.
 * 
 * arguments:
 * - method: The HTTP method e.g. 'PUT', 'POST', 'DELETE',
 * 
 * options:
 * - method:
 */
function constructForm(url, method, options={}) {

    method = method.toUpperCase();

    // Store the method in the options struct
    options.method = method;

    // Request OPTIONS endpoint from the API
    getApiEndpointOptions(url, function(OPTIONS) {

        /*
         * Determine what "type" of form we want to construct,
         * based on the requested action.
         * 
         * First we must determine if the user has the correct permissions!
         */

        switch (method) {
            case 'POST':
                if (canCreate(OPTIONS)) {
                    constructCreateForm(url, OPTIONS.actions.POST, options);
                } else {
                    // User does not have permission to POST to the endpoint
                    console.log('cannot POST');
                    // TODO
                }
                break;
            case 'PUT':
            case 'PATCH':
                if (canChange(OPTIONS)) {
                    constructChangeForm(url, OPTIONS.actions.PUT, options);
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
                console.log(`constructForm() called with invalid method '${method}'`);
                break;
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
function constructCreateForm(url, fields, options={}) {

    var html = '';

    var allowed_fields = options.fields || null;
    var ignored_fields = options.ignore || [];

    if (!ignored_fields.includes('pk')) {
        ignored_fields.push('pk');
    }

    if (!ignored_fields.includes('id')) {
        ignored_fields.push('id');
    }

    // Construct an ordered list of field names
    var field_names = [];

    if (allowed_fields) {
        allowed_fields.forEach(function(name) {

            // Only push names which are actually in the set of fields
            if (name in fields) {

                if (!ignored_fields.includes(name) && !field_names.includes(name)) {
                    field_names.push(name);
                }
            } else {
                console.log(`WARNING: '${name}' does not match a valid field name.`);
            }
        });
    } else {
        for (const name in fields) {

            if (!ignored_fields.includes(name) && !field_names.includes(name)) {
                field_names.push(name);
            }
        }
    }

    field_names.forEach(function(name) {

        var field = fields[name];
        
        var f = constructField(name, field, options);
        
        html += f;
    });

    var modal = '#modal-form';

    modalEnable(modal, true);

    $(modal).find('.modal-form-content').html(html);

    $(modal).modal('show');

    attachToggle(modal);
    attachSelect(modal);
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
function constructChangeForm(url, fields, options={}) {

    // Request existing data from the API endpoint
    $.ajax({
        url: url,
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

            constructCreateForm(url, fields, options);
        },
        error: function(request, status, error) {
            // TODO: Handle error here
            console.log(`ERROR in constructChangeForm at '${url}'`);
        }
    })

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

    var field_name = `id_${name}`;

    var form_classes = 'form-group';

    if (parameters.errors) {
        form_classes += ' has-error';
    }

    var html = `<div id='div_${field_name}' class='${form_classes}'>`;

    // Add a label
    html += constructLabel(name, parameters);

    html += `<div class='controls'>`;
    
    html += constructInput(name, parameters, options);

    if (parameters.errors) {
        html += constructErrorMessage(name, parameters, options);
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
function constructInput(name, parameters, options={}) {

    var html = '';

    var func = null;

    switch (parameters.type) {
        case 'boolean':
            func = constructCheckboxInput;
            break;
        case 'string':
            func = constructTextInput;
            break;
        case 'url':
            func = constructTextInput;
            break;
        case 'email':
            func = constructTextInput;
            break;
        case 'integer':
            func = constructNumberInput;
            break;
        case 'float':
            func = constructNumberInput;
            break;
        case 'decimal':
            func = constructNumberInput;
            break;
        case 'choice':
            func = constructChoiceInput;
            break;
        case 'field':
            // TODO: foreign key field!
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
function constructCheckboxInput(name, parameters, options={}) {

    return constructInputOptions(
        name,
        'checkboxinput',
        'checkbox',
        parameters
    );

}


// Construct a "text" input
function constructTextInput(name, parameters, options={}) {

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
function constructNumberInput(name, parameters, options={}) {

    return constructInputOptions(
        name,
        'numberinput form-control',
        'number',
        parameters
    );
}


// Construct a "choice" input
function constructChoiceInput(name, parameters, options={}) {

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
 * Construct a 'help text' div based on the field parameters
 * 
 * arguments:
 * - name: The name of the field
 * - parameters: Field parameters returned by the OPTIONS method
 *  
 */
function constructHelpText(name, parameters, options={}) {
    
    var html = `<div id='hint_id_${name}' class='help-block'>${parameters.help_text}</div>`;

    return html;
}


/*
 * Construct an 'error message' div for the field
 *
 * arguments:
 * - name: The name of the field
 * - parameters: Field parameters returned by the OPTIONS method
 */
function constructErrorMessage(name, parameters, options={}) {

    var errors_html = '';

    for (var idx = 0; idx < parameters.errors.length; idx++) {
        
        var err = parameters.errors[idx];

        var html = '';
        
        html += `<span id='error_${idx+1}_id_${name}' class='help-block'>`;
        html += `<strong>${err}</strong>`;
        html += `</span>`;

        errors_html += html;

    }

    return errors_html;
}