function makeOption(id, title) {
    return "<option value='" + id + "'>" + title + "</option>";
}

function attachSelect(modal) {

    // Attach to any 'select' inputs on the modal
    // Provide search filtering of dropdown items
    $(modal + ' .select').select2({
        dropdownParent: $(modal),
        dropdownAutoWidth: true,
    });
}

function afterForm(response, options) {

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
    $(modal + ' #modal-title').html(title);
}

function modalSetContent(modal, content='') {
    $(modal).find('.modal-form-content').html(content);
}

function modalSetButtonText(modal, submit_text, close_text) {
    $(modal).find("#modal-form-submit").html(submit_text);
    $(modal).find("#modal-form-close").html(close_text);
}

function closeModal(modal='#modal-form') {
    $(modal).modal('hide');
}

function modalSubmit(modal, callback) {
    $(modal).off('click', '#modal-form-submit');

    $(modal).on('click', '#modal-form-submit', function() {
        callback();
    });
}


function openModal(options) {

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
    // Inject the form data into the modal window
    $(modal).find('.modal-form-content').html(form_html);
    attachSelect(modal);
}

function handleModalForm(url, options) {

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

/*
 * launchModalForm
 * Opens a model window and fills it with a requested form
 * If the form is loaded successfully, calls handleModalForm
 */
function launchModalForm(url, options = {}) {

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