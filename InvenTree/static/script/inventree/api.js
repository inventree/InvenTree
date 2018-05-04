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

function getParts(filters={}) {
    return inventreeGet('/api/part/', filters);
}