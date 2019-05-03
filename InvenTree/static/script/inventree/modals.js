function makeOption(id, title) {
    /* Format an option for a select element
     */
    return "<option value='" + id + "'>" + title + "</option>";
}


function attachSelect(modal) {
    /* Attach 'select2' functionality to any drop-down list in the modal. 
     * Provides search filtering for dropdown items
     */

     $(modal + ' .select').select2({
        dropdownParent: $(modal),
        // dropdownAutoWidth parameter is required to work properly with modal forms
        dropdownAutoWidth: true,
    });
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
        showAlertOrCache("alert-success", response.success, cache);
    }
    if (response.info) {
        showAlertOrCache("alert-info", response.info, cache);
    }
    if (response.warning) {
        showAlertOrCache("alert-warning", response.warning, cache);
    }
    if (response.danger) {
        showAlertOrCache("alert-danger", response.danger, cache);
    }

    // Was a callback provided?
    if (options.success) {
        options.success();
    }
    else if (options.follow && response.url) {
        window.location.href = response.url;
    }
    else if (options.redirect) {
        window.location.href = options.redirect;
    }
    else if (options.reload) {
        location.reload();
    }

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


function modalSetButtonText(modal, submit_text, close_text) {
    /* Set the button text for a modal form
     * 
     * submit_text - text for the form submit button
     * close_text - text for the form dismiss button
     */
    $(modal).find("#modal-form-submit").html(submit_text);
    $(modal).find("#modal-form-close").html(close_text);
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

    $(modal).on('shown.bs.modal', function() {
        $(modal + ' .modal-form-content').scrollTop(0);
    });

    // Prevent 'enter' key from submitting the form using the normal method
    $(modal).on('keydown', '.js-modal-form', function(event) {
        if (event.keyCode == 13) {
            event.preventDefault();

            // Simulate a click on the 'Submit' button
            $(modal).find("#modal-form-submit").click();

            return false;
        }
    });

    if (options.title) {
        modalSetTitle(modal, options.title);
    }

    if (options.content) {
        modalSetContent(modal, options.content);
    }

    // Default labels for 'Submit' and 'Close' buttons in the form
    var submit_text = options.submit_text || 'Submit';
    var close_text = options.close_text || 'Close';

    modalSetButtonText(modal, submit_text, close_text);

    $(modal).modal({
        backdrop: 'static',
        keyboard: false,
    });
    $(modal).modal('show');
}


function launchDeleteForm(url, options = {}) {
    /* Launch a modal form to delete an object
     */

    var modal = options.modal || '#modal-delete';

    $(modal).on('shown.bs.modal', function() {
        $(modal + ' .modal-form-content').scrollTop(0);
    });

    // Un-bind any attached click listeners
    $(modal).off('click', '#modal-form-delete');

    // Request delete form data
    $.ajax({
        url: url,
        type: 'get',
        dataType: 'json',
        beforeSend: function() {
            openModal({modal: modal});
        },
        success: function (response) {
            if (response.title) {
                modalSetTitle(modal, response.title);
            }
            if (response.html_data) {
                modalSetContent(modal, response.html_data);
            }
            else {
                alert('JSON response missing HTML data');
                $(modal).modal('hide');
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            alert('Error requesting JSON data:\n' + thrownError);
            $(modal).modal('hide');
        }
    });

    $(modal).on('click', '#modal-form-delete', function() {

        var form = $(modal).find('#delete-form');

        $.ajax({
            url: url,
            data: form.serialize(),
            type: 'post',
            dataType: 'json',
            success: function (response) {
                $(modal).modal('hide');
                afterForm(response, options);
            },
            error: function (xhr, ajaxOptions, thrownError) {
                alert('Error deleting item:\n' + thrownError);
                $(modal).modal('hide');
            }
        });
    });
}


function injectModalForm(modal, form_html) {
    /* Inject form content into the modal.
     * Updates the HTML of the form content, and then applies some other updates
     */
    $(modal).find('.modal-form-content').html(form_html);
    attachSelect(modal);
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

    var _form = $(modal).find(".js-modal-form");

    form.ajaxForm({
        url: url,
        dataType: 'json',
        type: 'post'
    });

    form.submit(function() {
        alert('form submit');
        return false;
    });

    modalSubmit(modal, function() {
        $(modal).find('.js-modal-form').ajaxSubmit({
            url: url,
            // POST was successful
            success: function(response, status, xhr, f) {
                if ('form_valid' in response) {
                    // Form data was validated correctly
                    if (response.form_valid) {
                        $(modal).modal('hide');
                        afterForm(response, options);
                    }
                    // Form was returned, invalid!
                    else {
                        if (response.html_form) {
                            injectModalForm(modal, response.html_form);
                        }
                        else {
                            alert('HTML form data missing from server response');
                        }
                    }
                }
                else {
                    $(modal).modal('hide');
                    afterForm(response, options);
                }
            },
            error: function(xhr, ajaxOptions, thrownError) {
                alert('Error posting form data:\n' + thrownError);
                $(modal).modal('hide');
            },
            complete: function(xhr) {
                //TODO
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
     */

    var modal = options.modal || '#modal-form';

    // Default labels for 'Submit' and 'Close' buttons in the form
    var submit_text = options.submit_text || 'Submit';
    var close_text = options.close_text || 'Close';

    // Form the ajax request to retrieve the django form data
    ajax_data = {
        url: url,
        type: 'get',
        dataType: 'json',
        beforeSend: function () {
            openModal({
                modal: modal,
                submit_text: submit_text,
                close_text: close_text,
            });
        },
        success: function(response) {
            if (response.title) {
                modalSetTitle(modal, response.title);
            }

            if (response.html_form) {
                injectModalForm(modal, response.html_form);
                handleModalForm(url, options);

            } else {
                alert('JSON response missing form data');
                $(modal).modal('hide');
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            alert('Error requesting form data:\n' + thrownError);
            $(modal).modal('hide');
        }
    };

    // Add in extra request data if provided
    if (options.data) {
        ajax_data.data = options.data;
    }

    // Send the AJAX request
    $.ajax(ajax_data);
}
