/* Part API functions
 * Requires api.js to be loaded first
 */

function getPartCategoryList(filters={}, options={}) {
    return inventreeGet('/api/part/category/', filters, options);
}

function getSupplierPartList(filters={}, options={}) {
    return inventreeGet('/api/part/supplier/', filters, options);
}

function getPartList(filters={}, options={}) {
    return inventreeGet('/api/part/', filters, options);
}

function getBomList(filters={}, options={}) {
    return inventreeGet('/api/bom/', filters, options);
}