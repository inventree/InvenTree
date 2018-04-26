function attachSelect(modal) {

    // Attach to any 'select' inputs on the modal
    // Provide search filtering of dropdown items
    $(modal + ' .select').select2({
        dropdownParent: $(modal),
        dropdownAutoWidth: true,
    });
}

function launchDeleteForm(modal, url, options) {
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

                if (options.redirect) {
                    window.location.href = options.redirect;
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                alert('Error deleting item:\n' + thrownError);
                $(modal).modal('hide');
            }
        });
    });
}

function launchModalForm(modal, url, data, options) {

    $(modal).on('shown.bs.modal', function () {
        $(modal + ' .modal-form-content').scrollTop(0);
    });

    $.ajax({
        url: url,       // Where to request the data from
        type: 'get',    // GET request
        data: data,     // Any additional context data (e.g. initial values)
        dataType: 'json',
        beforeSend: function() {
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
    });

    $(modal).on('click', '#modal-form-submit', function() {

        // Extract the form from the modal dialog
        var form = $(modal).find(".js-modal-form");

        $.ajax({
            url: url,
            data: form.serialize(),
            type: form.attr('method'),
            dataType: 'json',
            success: function (response) {
                if (response.form_valid) {
                    alert("Success!");
                    $(modal).modal('hide');
                }
                else if (response.html_form) {
                    var target = modal + ' .modal-form-content';
                    $(target).html(response.html_form);

                    attachSelect(modal);
                }
                else {
                    alert('JSON response missing form data');
                    $(modal).modal('hide');
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