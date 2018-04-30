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

function launchDeleteForm(modal, url, options = {}) {

    $(modal).on('shown.bs.modal', function() {
        $(modal + ' .modal-form-content').scrollTop(0);
    });

    $.ajax({
        url: url,
        type: 'get',
        dataType: 'json',
        beforeSend: function() {
            $(modal).modal('show');
        },
        success: function (response) {
            if (response.title) {
                $(modal + ' #modal-title').html(response.title);
            }
            if (response.html_data) {
                $(modal + ' .modal-form-content').html(response.html_data);
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

function launchModalForm(modal, url, options = {}) {

    $(modal).on('shown.bs.modal', function () {
        $(modal + ' .modal-form-content').scrollTop(0);
    });

    // Prevent 'enter' key from submitting the form using the normal method
    $(modal).on('keydown', '.js-modal-form', function(event) {
        if (event.keyCode == 13) {
            event.preventDefault();

            $(modal).find("#modal-form-submit").click();

            return false;
        }
    });

    ajax_data = {
        url: url,
        type: 'get',
        dataType: 'json',
        beforeSend: function () {
            $(modal).modal('show');
        },
        success: function(response) {
            if (response.title) {
                $(modal + ' #modal-title').html(response.title);
            }
            if (response.submit_text) {
                $(modal + ' #modal-form-submit').html(response.submit_text);
            }
            if (response.html_form) {
                var target = modal + ' .modal-form-content';
                $(target).html(response.html_form);

                attachSelect(modal);

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

    $(modal).on('click', '#modal-form-submit', function() {

        // Extract the form from the modal dialog
        var form = $(modal).find(".js-modal-form");

        $.ajax({
            url: url,
            data: form.serialize(),
            type: form.attr('method'),
            dataType: 'json',
            success: function (response) {

                // Form validation was performed
                if ('form_valid' in response) {
                    if (response.form_valid) {
                        $(modal).modal('hide');
                        afterForm(response, options);
                    }
                    // Form was invalid - try again!
                    else {
                        if (response.html_form) {
                            $(modal + ' .modal-form-content').html(response.html_form);
                            attachSelect(modal);
                        }
                        else {
                            alert('HTML form data missing from AJAX response');
                        }
                    }
                }
                else {
                    $(modal).modal('hide');
                    afterForm(response, options);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                alert("Error posting form data:\n" + thrownError);
                $(modal).modal('hide');
            }
        });

        // Override the default form submit functionality
        return false;
    });
}