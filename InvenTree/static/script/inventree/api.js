function inventreeGet(url, filters={}) {
    $.ajax({
        url: url,
        type: 'get',
        data: filters,
        dataType: 'json',
        success: function(response) {
            console.log('Success GET data at ' + url);
            return response;
        },
        error: function(xhr, ajaxOptions, thrownError) {
            console.error('Error on GET at ' + url);
            console.error(thrownError);
            return {};
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