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