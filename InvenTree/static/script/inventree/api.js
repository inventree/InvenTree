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

function inventreeGet(url, filters={}) {
    $.ajax({
        url: url,
        type: 'GET',
        data: filters,
        dataType: 'json',
        success: function(response) {
            console.log('Success GET data at ' + url);
            return response;
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.error('Error on GET at ' + url);
            console.error(thrownError);
            return {error: thrownError};
        }
    })
}

function inventreeUpdate(url, data, final=false) {
    if (final) {
        data["_is_final"] = true;
    }

    // Middleware token required for data update
    //var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    var csrftoken = getCookie('csrftoken');

    $.ajax({
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader('X-CSRFToken', csrftoken);
        },
        url: url,
        type: 'put',
        data: data,
        dataType: 'json',
        success: function(response, status) {
            response['_status_code'] = status;
            console.log('UPDATE object to ' + url + ' - result = ' + status);
            return response;
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.error('Error on UPDATE to ' + url);
            console.error(thrownError);
            return {error: thrownError};
        }
    })
}

// Return list of parts with optional filters
function getParts(filters={}) {
    return inventreeGet('/api/part/', filters);
}

// Return list of part categories with optional filters
function getPartCategories(filters={}) {
    return inventreeGet('/api/part/category/', filters);
}

function getStock(filters={}) {
    return inventreeGet('/api/stock/', filters);
}

function getStockLocations(filters={}) {
    return inventreeGet('/api/stock/location/', filters)
}

function getCompanies(filters={}) {
    return inventreeGet('/api/company/', filters);
}