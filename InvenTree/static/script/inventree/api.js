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
            console.log('Success GET data at ' + url);
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

function inventreeUpdate(url, data={}, options={}) {
    if ('final' in options && options.final) {
        data["_is_final"] = true;
    }

    var method = 'put';

    if ('method' in options) {
        method = options.method;
    }

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
            response['_status_code'] = status;
            console.log('UPDATE object to ' + url + ' - result = ' + status);
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.error('Error on UPDATE to ' + url);
            console.error(thrownError);
            }
        });
}

// Return list of parts with optional filters
function getParts(filters={}, options={}) {
    return inventreeGet('/api/part/', filters, options);
}

// Return list of part categories with optional filters
function getPartCategories(filters={}, options={}) {
    return inventreeGet('/api/part/category/', filters, options);
}

function getCompanies(filters={}, options={}) {
    return inventreeGet('/api/company/', filters, options);
}

function updateStockItem(pk, data, final=false) {
    return inventreeUpdate('/api/stock/' + pk + '/', data, final);
}

function updatePart(pk, data, final=false) {
    return inventreeUpdate('/api/part/' + pk + '/', data, final);
}