{% load i18n %}

/* globals
    inventreeGet,
    showAlertOrCache,
*/

/* exported
    attachSecondaryModal,
    clearField,
    clearFieldOptions,
    closeModal,
    enableField,
    enableSubmitButton,
    getFieldValue,
    reloadFieldOptions,
    showModalImage,
    showQuestionDialog,
    showModalSpinner,
*/

/*
 * Create and display a new modal dialog
 *
 * options:
 * - title: Form title to render
 * - submitText: Text to render on 'submit' button (default = "Submit")
 * - closeText: Text to render on 'close' button (default = "Cancel")
 * - focus: Name of field to focus on after launching
 */
function createNewModal(options={}) {

    var id = 1;

    // Check out what modal forms are already being displayed
    $('.inventree-modal').each(function() {

        var split = this.id.split('-');
        var modal_id = parseInt(split[2]);

        if (modal_id >= id) {
            id = modal_id + 1;
        }
    });

    var submitClass = options.submitClass || 'primary';

    var html = `
    <div class='modal fade modal-fixed-footer modal-primary inventree-modal' role='dialog' id='modal-form-${id}' tabindex='-1'>
        <div class='modal-dialog'>
            <div class='modal-content'>
                <div class="modal-header">
                    <h4 id='modal-title' class='modal-title'>
                        <!-- Form title to be injected here -->
                    </h4>
                    <button type='button' class='btn-close' data-bs-dismiss='modal' aria-label='{% trans "Close" %}'></button>
                </div>
                <div class='modal-body modal-form-content-wrapper'>
                    <div id='non-field-errors'>
                        <!-- Form error messages go here -->
                    </div>
                    <div id='pre-form-content'>
                        <!-- Content can be inserted here *before* the form fields -->
                    </div>

                    <div id='form-content' class='modal-form-content'>
                        <!-- Form content will be injected here-->
                    </div>
                    <div id='post-form-content'>
                        <!-- Content can be inserted here *after* the form fields -->
                    </div>
                </div>
                <div class='modal-footer'>
                    <div id='modal-footer-buttons'>
                        <!-- Extra buttons can be inserted here -->
                    </div>
                    <span class='flex-item' style='flex-grow: 1;'></span>
                    <h4><span id='modal-progress-spinner' class='fas fa-circle-notch fa-spin' style='display: none;'></span></h4>
                    <div id='modal-footer-secondary-buttons'>
                        <!-- Extra secondary buttons can be inserted here -->
                    </div>
                    <button type='button' class='btn btn-secondary' id='modal-form-close' data-bs-dismiss='modal'>{% trans "Cancel" %}</button>
                    <button type='button' class='btn btn-${submitClass}' id='modal-form-submit'>{% trans "Submit" %}</button>
                </div>
            </div>
        </div>
    </div>
    `;

    $('body').append(html);

    var modal_name = `#modal-form-${id}`;

    // Callback *after* the modal has been rendered
    $(modal_name).on('shown.bs.modal', function() {
        $(modal_name + ' .modal-form-content').scrollTop(0);

        if (options.focus) {
            getFieldByName(modal_name, options.focus).focus();
        }

        // Steal keyboard focus
        $(modal_name).focus();

        if (options.hideCloseButton) {
            $(modal_name).find('#modal-form-close').hide();
        }

        if (options.preventSubmit || options.hideSubmitButton) {
            $(modal_name).find('#modal-form-submit').hide();
        }

    });

    // Automatically remove the modal when it is deleted!
    $(modal_name).on('hidden.bs.modal', function() {
        $(modal_name).remove();
    });

    // Capture "enter" key input
    $(modal_name).on('keydown', 'input', function(event) {
        if (event.keyCode == 13) {
            event.preventDefault();

            if (!options.preventSubmit) {
                // Simulate a click on the 'Submit' button
                $(modal_name).find('#modal-form-submit').click();
            }

            return false;
        }
    });

    $(modal_name).modal({
        backdrop: 'static',
        keyboard: user_settings.FORMS_CLOSE_USING_ESCAPE,
    });

    // Set labels based on supplied options
    modalSetTitle(modal_name, options.title || '{% trans "Form Title" %}');
    modalSetSubmitText(modal_name, options.submitText || '{% trans "Submit" %}');
    modalSetCloseText(modal_name, options.closeText || '{% trans "Cancel" %}');

    // Return the "name" of the modal
    return modal_name;
}


/*
 * Convenience function to enable (or disable) the "submit" button on a modal form
 */
function enableSubmitButton(options, enable=true) {

    if (!options || !options.modal) {
        console.warn('enableSubmitButton() called without modal reference');
        return;
    }

    if (enable) {
        $(options.modal).find('#modal-form-submit').prop('disabled', false);
    } else {
        $(options.modal).find('#modal-form-submit').prop('disabled', true);
    }
}


function makeOption(text, value, title) {
    /* Format an option for a select element
     */

    var html = `<option value='${value || text}'`;

    if (title) {
        html += ` title='${title}'`;
    }

    html += `>${text}</option>`;

    return html;
}

function makeOptionsList(elements, textFunc, valueFunc, titleFunc) {
    /*
     * Programatically generate a list of <option> elements,
     * from the (assumed array) of elements.
     * For each element, we pass the element to the supplied functions,
     * which (in turn) generate display / value / title values.
     *
     * Args:
     * - elements: List of elements
     * - textFunc: Function which takes an element and generates the text to be displayed
     * - valueFunc: optional function which takes an element and generates the value
     * - titleFunc: optional function which takes an element and generates a title
     */

    var options = [];

    elements.forEach(function(element) {

        var text = textFunc(element);
        var value = null;
        var title = null;

        if (valueFunc) {
            value = valueFunc(element);
        } else {
            value = text;
        }

        if (titleFunc) {
            title = titleFunc(element);
        }

        options.push(makeOption(text, value, title));
    });

    return options;
}


function setFieldOptions(fieldName, optionList, options={}) {
    /* Set the options for a <select> field.
     *
     * Args:
     * - fieldName: The name of the target field
     * - Options: List of formatted <option> strings
     * - append: If true, options will be appended, otherwise will replace existing options.
     */


    var append = options.append || false;

    var modal = options.modal || '#modal-form';

    var field = getFieldByName(modal, fieldName);

    var addEmptyOption = options.addEmptyOption || true;

    // If not appending, clear out the field...
    if (!append) {
        field.find('option').remove();
    }

    if (addEmptyOption) {
        // Add an 'empty' option at the top of the list
        field.append(`<option value="">---------</option>`);
    }

    optionList.forEach(function(option) {
        field.append(option);
    });

}


function clearFieldOptions(fieldName) {
    /**
     * Clear (emtpy) the options list for a particular field
     */

    setFieldOptions(fieldName, []);
}


function reloadFieldOptions(fieldName, options) {
    /* Reload the options for a given field,
     * using an AJAX request.
     *
     * Args:
     * - fieldName: The name of the field
     * - options:
     * -- url: Query url
     * -- params: Query params
     * -- value: A function which takes a returned option and returns the 'value' (if not specified, the `pk` field is used)
     * -- text: A function which takes a returned option and returns the 'text'
     * -- title: A function which takes a returned option and returns the 'title' (optional!)
     */

    inventreeGet(options.url, options.params, {
        success: function(response) {
            var opts = makeOptionsList(response,
                function(item) {
                    return options.text(item);
                },
                function(item) {
                    if (options.value) {
                        return options.value(item);
                    } else {
                        // Fallback is to use the 'pk' field
                        return item.pk;
                    }
                },
                function(item) {
                    if (options.title) {
                        return options.title(item);
                    } else {
                        return null;
                    }
                }
            );

            // Update the target field with the new options
            setFieldOptions(fieldName, opts);
        },
        error: function() {
            console.error('Error GETting field options');
        }
    });
}


function enableField(fieldName, enabled, options={}) {
    /* Enable (or disable) a particular field in a modal.
     *
     * Args:
     * - fieldName: The name of the field
     * - enabled: boolean enabled / disabled status
     * - options:
     */

    var modal = options.modal || '#modal-form';

    var field = getFieldByName(modal, fieldName);

    field.prop('disabled', !enabled);
}

function clearField(fieldName, options={}) {

    setFieldValue(fieldName, '', options);
}

function setFieldValue(fieldName, value, options={}) {

    var modal = options.modal || '#modal-form';

    var field = getFieldByName(modal, fieldName);

    field.val(value);
}

function getFieldValue(fieldName, options={}) {

    var modal = options.modal || '#modal-form';

    var field = getFieldByName(modal, fieldName);

    return field.val();
}


function partialMatcher(params, data) {
    /* Replacement function for the 'matcher' parameter for a select2 dropdown.

    Intead of performing an exact match search, a partial match search is performed.
    This splits the search term by the space ' ' character and matches each segment.
    Segments can appear out of order and are not case sensitive

    Args:
        params.term : search query
        data.text : text to match
    */

    // Quickly check for an empty search query
    if ($.trim(params.term) == '') {
        return data;
    }

    // Do not display the item if there is no 'text' property
    if (typeof data.text === 'undefined') {
        return null;
    }

    var search_terms = params.term.toLowerCase().trim().split(' ');

    var match_text = data.text.toLowerCase().trim();

    for (var ii = 0; ii < search_terms.length; ii++) {
        if (!match_text.includes(search_terms[ii])) {
            // Text must contain each search term
            return null;
        }
    }

    // Default: match!
    return data;
}


function attachSelect(modal) {
    /* Attach 'select2' functionality to any drop-down list in the modal.
     * Provides search filtering for dropdown items
     */

    $(modal + ' .select').select2({
        dropdownParent: $(modal),
        // dropdownAutoWidth parameter is required to work properly with modal forms
        dropdownAutoWidth: false,
        matcher: partialMatcher,
    });

    $(modal + ' .select2-container').addClass('select-full-width');
    $(modal + ' .select2-container').css('width', '100%');
}


function attachBootstrapCheckbox(modal) {
    /* Attach 'switch' functionality to any checkboxes on the form */

    $(modal + ' .checkboxinput').addClass('form-check-input');
    $(modal + ' .checkboxinput').wrap(`<div class='form-check form-switch'></div>`);
}


function loadingMessageContent() {
    /* Render a 'loading' message to display in a form
     * when waiting for a response from the server
     */

    // TODO - This can be made a lot better
    return `<span class='glyphicon glyphicon-refresh glyphicon-refresh-animate'></span> {% trans 'Waiting for server...' %}`;
}


function afterForm(response, options) {
    /* afterForm is called after a form is successfully submitted,
     * and the form is dismissed.
     * Used for general purpose functionality after form submission:
     *
     * - Display a bootstrap alert (success / info / warning / danger)
     * - Run a supplied success callback function
     * - Redirect the browser to a different URL
     * - Reload the page
     */

    // Should we show alerts immediately or cache them?
    var cache = (options.follow && response.url) ||
                options.redirect ||
                options.reload;

    // Display any messages
    if (response.success) {
        showAlertOrCache(response.success, cache, {style: 'success'});
    }

    if (response.info) {
        showAlertOrCache(response.info, cache, {style: 'info'});
    }

    if (response.warning) {
        showAlertOrCache(response.warning, cache, {style: 'warning'});
    }

    if (response.danger) {
        showAlertOrCache(response.danger, cache, {style: 'danger'});
    }

    // Was a callback provided?
    if (options.success) {
        options.success(response);
    } else if (options.follow && response.url) {
        window.location.href = response.url;
    } else if (options.redirect) {
        window.location.href = options.redirect;
    } else if (options.reload) {
        location.reload();
    }
}

function modalShowSubmitButton(modal, show=true) {
    /* Show (or hide) the 'Submit' button for the given modal form
     */

    if (show) {
        $(modal).find('#modal-form-submit').show();
    } else {
        $(modal).find('#modal-form-submit').hide();
    }
}


function modalEnable(modal, enable=true) {
    /* Enable (or disable) modal form elements to prevent user input
     */

    // Enable or disable the submit button
    $(modal).find('#modal-form-submit').prop('disabled', !enable);
}


function modalSetTitle(modal, title='') {
    /* Update the title of a modal form
     */
    $(modal + ' #modal-title').html(title);
}


function modalSetContent(modal, content='') {
    /* Update the content panel of a modal form
     */
    $(modal).find('.modal-form-content').html(content);
}


function modalSetSubmitText(modal, text) {
    if (text) {
        $(modal).find('#modal-form-submit').html(text);
    }
}


function modalSetCloseText(modal, text) {
    if (text) {
        $(modal).find('#modal-form-close').html(text);
    }
}


function modalSetButtonText(modal, submit_text, close_text) {
    /* Set the button text for a modal form
     *
     * submit_text - text for the form submit button
     * close_text - text for the form dismiss button
     */
    modalSetSubmitText(modal, submit_text);
    modalSetCloseText(modal, close_text);
}


function closeModal(modal='#modal-form') {
    /* Dismiss (hide) a modal form
     */
    $(modal).modal('hide');
}


function modalSubmit(modal, callback) {
    /* Perform the submission action for the modal form
     */
    $(modal).off('click', '#modal-form-submit');

    $(modal).on('click', '#modal-form-submit', function() {
        callback();
    });

    $(modal).on('click', '.modal-form-button', function() {
        // Append data to form
        var name = $(this).attr('name');
        var value = $(this).attr('value');
        var input = '<input id="id_act-btn_' + name + '" type="hidden" name="act-btn_' + name + '" value="' + value + '">';
        $('.js-modal-form').append(input);
        callback();
    });
}


function renderErrorMessage(xhr) {

    var html = '<b>' + xhr.statusText + '</b><br>';

    html += '<b>Error Code - ' + xhr.status + '</b><br><hr>';

    html += `
    <div class='panel-group'>
        <div class='panel'>
            <div class='panel panel-heading'>
                <div class='panel-title'>
                    <a data-bs-toggle='collapse' href="#collapse-error-info">{% trans "Show Error Information" %}</a>
                </div>
            </div>
            <div class='panel-collapse collapse' id='collapse-error-info'>
                <div class='panel-content'>`;

    html += xhr.responseText;

    html += `
                </div>
            </div>
        </div>
    </div>`;

    return html;
}


function showAlertDialog(title, content, options={}) {
    /* Display a modal dialog message box.
     *
     * title - Title text
     * content - HTML content of the dialog window
     */

    if (options.alert_style) {
        // Wrap content in an alert block
        content = `<div class='alert alert-block alert-${options.alert_style}'>${content}</div>`;
    }


    var modal = createNewModal({
        title: title,
        closeText: '{% trans "Close" %}',
        hideSubmitButton: true,
    });

    modalSetContent(modal, content);

    $(modal).modal('show');
}


function showQuestionDialog(title, content, options={}) {
    /* Display a modal dialog for user input (Yes/No confirmation dialog)
     *
     * title - Title text
     * content - HTML content of the dialog window
     * options:
     *   modal - Modal target (default = 'modal-question-dialog')
     *   accept_text - Text for the accept button (default = 'Accept')
     *   cancel_text - Text for the cancel button (default = 'Cancel')
     *   accept - Function to run if the user presses 'Accept'
     *   cancel - Functino to run if the user presses 'Cancel'
     */

    var modal = createNewModal({
        title: title,
        submitText: options.accept_text || '{% trans "Accept" %}',
        closeText: options.cancel_text || '{% trans "Cancel" %}',
    });

    modalSetContent(modal, content);

    $(modal).on('click', '#modal-form-submit', function() {
        $(modal).modal('hide');

        if (options.accept) {
            options.accept();
        }
    });

    $(modal).modal('show');
}

function openModal(options) {
    /* Open a modal form, and perform some action based on the provided options object:
     *
     * options can contain:
     *
     * modal - ID of the modal form element (default = '#modal-form')
     * title - Custom title for the form
     * content - Default content for the form panel
     * submit_text - Label for the submit button (default = 'Submit')
     * close_text - Label for the close button (default = 'Close')
     */

    var modal = options.modal || '#modal-form';

    // Ensure that the 'warning' div is hidden
    $(modal).find('#form-validation-warning').css('display', 'none');

    $(modal).on('shown.bs.modal', function() {
        $(modal + ' .modal-form-content').scrollTop(0);
        if (options.focus) {
            getFieldByName(modal, options.focus).focus();
        }
    });

    // Prevent 'enter' key from submitting the form using the normal method
    $(modal).on('keydown', '.js-modal-form', function(event) {
        if (event.keyCode == 13) {
            event.preventDefault();

            // Simulate a click on the 'Submit' button
            $(modal).find('#modal-form-submit').click();

            return false;
        }
    });

    // Unless the title is explicitly set, display loading message
    if (options.title) {
        modalSetTitle(modal, options.title);
    } else {
        modalSetTitle(modal, '{% trans "Loading Data" %}...');
    }

    // Unless the content is explicitly set, display loading message
    if (options.content) {
        modalSetContent(modal, options.content);
    } else {
        modalSetContent(modal, loadingMessageContent());
    }

    // Default labels for 'Submit' and 'Close' buttons in the form
    var submit_text = options.submit_text || '{% trans "Submit" %}';
    var close_text = options.close_text || '{% trans "Close" %}';

    modalSetButtonText(modal, submit_text, close_text);

    $(modal).modal({
        backdrop: 'static',
        keyboard: user_settings.FORMS_CLOSE_USING_ESCAPE,
    });

    // Disable the form
    modalEnable(modal, false);

    // Finally, display the modal window
    $(modal).modal('show');
}


function injectModalForm(modal, form_html) {
    /* Inject form content into the modal.
     * Updates the HTML of the form content, and then applies some other updates
     */
    $(modal).find('.modal-form-content').html(form_html);

    attachSelect(modal);
    attachBootstrapCheckbox(modal);
}


function getFieldByName(modal, name) {
    /* Find the field (with the given name) within the modal */

    return $(modal).find(`#id_${name}`);
}


function insertNewItemButton(modal, options) {
    /* Insert a button into a modal form, after a field label.
     * Looks for a <label> tag inside the form with the attribute "for='id_<field>'"
     * Inserts a button at the end of this lael element.
     */

    var html = `<span style='float: right;'>`;

    html += `<div type='button' class='btn btn-primary btn-secondary'`;

    if (options.title) {
        html += ` title='${ options.title}'`;
    }

    html += ` id='btn-new-${options.field}'>${options.label}</div>`;

    html += '</span>';

    $(modal).find('label[for="id_'+ options.field + '"]').append(html);
}


function attachSecondaryModal(modal, options) {
    /* Attach a secondary modal form to the primary modal form.
     * Inserts a button into the primary form which, when clicked,
     * will launch the secondary modal to do /something/ and then return a result.
     *
     * options:
     *  field: Name of the field to attach to
     *  label: Button text
     *  title: Hover text to display over button (optional)
     *  url: URL for the secondary modal
     *  query: Query params for the secondary modal
     */

    // Insert the button
    insertNewItemButton(modal, options);

    var data = options.data || {};

    // Add a callback to the button
    $(modal).find('#btn-new-' + options.field).on('click', function() {

        // Launch the secondary modal
        launchModalForm(
            options.url,
            {
                modal: '#modal-form-secondary',
                data: data,
                success: function(response) {

                    /* A successful object creation event should return a response which contains:
                     *  - pk: ID of the newly created object
                     *  - text: String descriptor of the newly created object
                     *
                     * So it is simply a matter of appending and selecting the new object!
                     */

                    var select = '#id_' + options.field;

                    var option = new Option(response.text, response.pk, true, true);

                    $(modal).find(select).append(option).trigger('change');
                }
            }
        );
    });
}


// eslint-disable-next-line no-unused-vars
function attachSecondaries(modal, secondaries) {
    /* Attach a provided list of secondary modals */

    // 2021-07-18 - Secondary modals will be disabled for now, until they are re-implemented in the "API forms" architecture

    // for (var i = 0; i < secondaries.length; i++) {
    //     attachSecondaryModal(modal, secondaries[i]);
    // }
}

function insertActionButton(modal, options) {
    /* Insert a custom submission button */

    var element = $(modal).find('#modal-footer-buttons');

    // check if button already present
    var already_present = false;
    for (var child=element[0].firstElementChild; child; child=child.nextElementSibling) {
        if (item.firstElementChild.name == options.name) {
            already_present = true;
        }
    }

    if (already_present == false) {
        var html = `
        <span style='float: right;'>
            <button name='${options.name}' type='submit' class='btn btn-outline-secondary modal-form-button' value='${options.name}'>
                ${options.title}
            </button>
        </span>`;
        element.append(html);
    }
}

function attachButtons(modal, buttons) {
    /* Attach a provided list of buttons */

    for (var i = 0; i < buttons.length; i++) {
        insertActionButton(modal, buttons[i]);
    }
}


function attachFieldCallback(modal, callback) {
    /* Attach a 'callback' function to a given field in the modal form.
     * When the value of that field is changed, the callback function is performed.
     *
     * options:
     * - field: The name of the field to attach to
     * - action: A function to perform
     */

    // Find the field input in the form
    var field = getFieldByName(modal, callback.field);

    field.change(function() {

        if (callback.action) {
            // Run the callback function with the new value of the field!
            callback.action(field.val(), field);
        } else {
            console.info(`Value changed for field ${callback.field} - ${field.val()} (no callback attached)`);
        }
    });
}


function attachCallbacks(modal, callbacks) {
    /* Attach a provided list of callback functions */

    for (var i = 0; i < callbacks.length; i++) {
        attachFieldCallback(modal, callbacks[i]);
    }
}


function handleModalForm(url, options) {
    /* Update a modal form after data are received from the server.
     * Manages POST requests until the form is successfully submitted.
     *
     * The server should respond with a JSON object containing a boolean value 'form_valid'
     * Form submission repeats (after user interaction) until 'form_valid' = true
     */

    var modal = options.modal || '#modal-form';

    var form = $(modal).find('.js-modal-form');

    form.ajaxForm({
        url: url,
        dataType: 'json',
        type: 'post'
    });

    form.submit(function() {
        // We should never get here (form submission is overridden)
        alert('form submit');
        return false;
    });

    modalSubmit(modal, function() {
        $(modal).find('.js-modal-form').ajaxSubmit({
            url: url,
            beforeSend: function() {
                // Disable modal until the server returns a response
                modalEnable(modal, false);
            },
            // POST was successful
            success: function(response) {
                // Re-enable the modal
                modalEnable(modal, true);
                if ('form_valid' in response) {
                    // Get visibility option of error message
                    var hideErrorMessage = (options.hideErrorMessage === undefined) ? true : options.hideErrorMessage;

                    // Form data was validated correctly
                    if (response.form_valid) {
                        $(modal).modal('hide');
                        afterForm(response, options);
                    } else {
                        // Form was returned, invalid!

                        // Disable error message with option or response
                        if (!hideErrorMessage && !response.hideErrorMessage) {
                            var warningDiv = $(modal).find('#form-validation-warning');
                            warningDiv.css('display', 'block');
                        }

                        if (response.html_form) {
                            injectModalForm(modal, response.html_form);

                            if (options.after_render) {
                                options.after_render(modal, response);
                            }

                            if (options.secondary) {
                                attachSecondaries(modal, options.secondary);
                            }

                            // Set modal title with response
                            if (response.title) {
                                modalSetTitle(modal, response.title);
                            }

                            // Clean custom action buttons
                            $(modal).find('#modal-footer-buttons').html('');

                            // Add custom action buttons with response
                            if (response.buttons) {
                                attachButtons(modal, response.buttons);
                            }
                        } else {
                            $(modal).modal('hide');
                            showAlertDialog('{% trans "Invalid response from server" %}', '{% trans "Form data missing from server response" %}');
                        }
                    }
                } else {
                    $(modal).modal('hide');
                    afterForm(response, options);
                }
            },
            error: function(xhr) {
                // There was an error submitting form data via POST

                $(modal).modal('hide');
                showAlertDialog('{% trans "Error posting form data" %}', renderErrorMessage(xhr));
            },
            complete: function() {
                // TODO
            }
        });
    });
}


function launchModalForm(url, options = {}) {
    /* Launch a modal form, and request data from the server to fill the form
     * If the form data is returned from the server, calls handleModalForm()
     *
     * A successful request will return a JSON object with, at minimum,
     * an object called 'html_form'
     *
     * If the request is NOT successful, displays an appropriate error message.
     *
     * options:
     *
     * modal - Name of the modal (default = '#modal-form')
     * data - Data to pass through to the AJAX request to fill the form
     * submit_text - Text for the submit button (default = 'Submit')
     * close_text - Text for the close button (default = 'Close')
     * no_post - If true, only display form data, hide submit button, and disallow POST
     * after_render - Callback function to run after form is rendered
     * secondary - List of secondary modals to attach
     * callback - List of callback functions to attach to inputs
     * focus - Select which field to focus on by default
     * buttons - additional buttons that should be added as array with [name, title]
     */

    var modal = options.modal || '#modal-form';

    // Default labels for 'Submit' and 'Close' buttons in the form
    var submit_text = options.submit_text || '{% trans "Submit" %}';
    var close_text = options.close_text || '{% trans "Close" %}';

    // Clean custom action buttons
    $(modal).find('#modal-footer-buttons').html('');

    // Form the ajax request to retrieve the django form data
    var ajax_data = {
        url: url,
        type: 'get',
        dataType: 'json',
        beforeSend: function() {
            openModal({
                modal: modal,
                submit_text: submit_text,
                close_text: close_text,
                focus: options.focus
            });
        },
        success: function(response) {

            // Enable the form
            modalEnable(modal, true);

            if (response.title) {
                modalSetTitle(modal, response.title);
            }

            if (response.html_form) {
                injectModalForm(modal, response.html_form);

                if (options.after_render) {
                    options.after_render(modal, response);
                }

                if (options.secondary) {
                    attachSecondaries(modal, options.secondary);
                }

                if (options.callback) {
                    attachCallbacks(modal, options.callback);
                }

                if (options.no_post) {
                    modalShowSubmitButton(modal, false);
                } else {
                    modalShowSubmitButton(modal, true);
                    handleModalForm(url, options);
                }

                if (options.buttons) {
                    attachButtons(modal, options.buttons);
                }

                // Add custom buttons from response
                if (response.buttons) {
                    attachButtons(modal, response.buttons);
                }

            } else {
                $(modal).modal('hide');
                showAlertDialog('{% trans "Invalid server response" %}', '{% trans "JSON response missing form data" %}');
            }
        },
        error: function(xhr) {

            $(modal).modal('hide');

            if (xhr.status == 0) {
                // No response from the server
                showAlertDialog(
                    '{% trans "No Response" %}',
                    '{% trans "No response from the InvenTree server" %}',
                );
            } else if (xhr.status == 400) {
                showAlertDialog(
                    '{% trans "Error 400: Bad Request" %}',
                    '{% trans "Server returned error code 400" %}',
                );
            } else if (xhr.status == 401) {
                showAlertDialog(
                    '{% trans "Error 401: Not Authenticated" %}',
                    '{% trans "Authentication credentials not supplied" %}',
                );
            } else if (xhr.status == 403) {
                showAlertDialog(
                    '{% trans "Error 403: Permission Denied" %}',
                    '{% trans "You do not have the required permissions to access this function" %}',
                );
            } else if (xhr.status == 404) {
                showAlertDialog(
                    '{% trans "Error 404: Resource Not Found" %}',
                    '{% trans "The requested resource could not be located on the server" %}',
                );
            } else if (xhr.status == 408) {
                showAlertDialog(
                    '{% trans "Error 408: Timeout" %}',
                    '{% trans "Connection timeout while requesting data from server" %}',
                );
            } else {
                showAlertDialog('{% trans "Error requesting form data" %}', renderErrorMessage(xhr));
            }

            console.error('Modal form error: ' + xhr.status);
            console.info('Message: ' + xhr.responseText);
        }
    };

    // Add in extra request data if provided
    if (options.data) {
        ajax_data.data = options.data;
    }

    // Send the AJAX request
    $.ajax(ajax_data);
}


function hideModalImage() {

    var modal = $('#modal-image-dialog');

    modal.animate({
        opacity: 0.0,
    }, 250, function() {
        modal.hide();
    });

}


function showModalImage(image_url) {
    // Display full-screen modal image

    var modal = $('#modal-image-dialog');

    // Set image content
    $('#modal-image').attr('src', image_url);

    modal.hide();
    modal.show();

    modal.animate({
        opacity: 1.0,
    }, 250);

    $('#modal-image-close').click(function() {
        hideModalImage();
    });

    modal.click(function() {
        hideModalImage();
    });
}


/* Show (or hide) a progress spinner icon in the dialog */
function showModalSpinner(modal, show=true) {
    if (show) {
        $(modal).find('#modal-progress-spinner').show();
    } else {
        $(modal).find('#modal-progress-spinner').hide();
    }
}
