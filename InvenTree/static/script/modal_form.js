function launchModalForm(modal, url, data) {

    $(modal).on('shown.bs.modal', function () {
        $(modal + ' .modal-content').scrollTop(0); // animate({ scrollTop: 0 }, 'fast');
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
            if (response.html_form) {
                var target = modal + ' .modal-content';
                $(target).html(response.html_form);

                var select = modal + ' .select';
                $(select).select2({
                    dropdownParent: $(modal),
                    dropdownAutoWidth: true
                });

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

    $(modal).on('submit', '.js-modal-form', function() {
        var form = $(this);

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
                    var target = modal + ' .modal-content';
                    $(target).html(response.html_form);

                    var select = modal + ' .select';
                    $(select).select2({
                        dropdownParent: $(modal),
                        dropdownAutoWidth: true
                    });
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