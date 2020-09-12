var jQuery = window.$;

// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function inventreeGet(url, filters={}, options={}) {
    return $.ajax({
        url: url,
        type: 'GET',
        data: filters,
        dataType: 'json',
        contentType: 'application/json',
        success: function(response) {
            if (options.success) {
                options.success(response);
            }
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.error('Error on GET at ' + url);
            console.error(thrownError);
            if (options.error) {
                options.error({
                    error: thrownError
                });
            }
        }
    });
}

function inventreeFormDataUpload(url, data, options={}) {
    /* Upload via AJAX using the FormData approach.
     * 
     * Note that the following AJAX parameters are required for FormData upload
     * 
     * processData: false
     * contentType: false
     */

    // CSRF cookie token
    var csrftoken = getCookie('csrftoken');

    return $.ajax({
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader('X-CSRFToken', csrftoken);
        },
        url: url,
        method: 'POST',
        data: data,
        processData: false,
        contentType: false,
        success: function(data, status, xhr) {
            if (options.success) {
                options.success(data, status, xhr);
            }
        },
        error: function(xhr, status, error) {
            console.log('Form data upload failure: ' + status);

            if (options.error) {
                options.error(xhr, status, error);
            }
        }
    });
}

function inventreePut(url, data={}, options={}) {

    var method = options.method || 'PUT';

    // Middleware token required for data update
    //var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    var csrftoken = getCookie('csrftoken');

    return $.ajax({
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader('X-CSRFToken', csrftoken);
        },
        url: url,
        type: method,
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: 'application/json',
        success: function(response, status) {
            if (options.success) {
                options.success(response, status);
            }
            if (options.reloadOnSuccess) {
                location.reload();
            }
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.error('Error on UPDATE to ' + url);
            console.error(thrownError);
            if (options.error) {
                options.error(xhr, ajaxOptions, thrownError);
            }
        },
        complete: function(xhr, status) {
            if (options.complete) {
                options.complete(xhr, status);
            }
        }
    });
}


function inventreeDelete(url, options={}) {
    /*
     * Delete a record
     */

    options = options || {};

    options.method = 'DELETE';

    inventreePut(url, {}, options);

}