{% load i18n %}

/* globals
    blankImage,
    select2Thumbnail
*/

/* exported
    renderBuild,
    renderCompany,
    renderManufacturerPart,
    renderOwner,
    renderPartCategory,
    renderStockLocation,
    renderSupplierPart,
*/


/*
 * This file contains functions for rendering various InvenTree database models,
 * in particular for displaying them in modal forms in a 'select2' context.
 * 
 * Each renderer is provided with three arguments:
 * 
 * - name: The 'name' of the model instance in the referring model
 * - data: JSON data which represents the model instance. Returned via a GET request.
 * - parameters: The field parameters provided via an OPTIONS request to the endpoint.
 * - options: User options provided by the client
 */


// Renderer for "Company" model
// eslint-disable-next-line no-unused-vars
function renderCompany(name, data, parameters, options) {
    
    var html = select2Thumbnail(data.image);

    html += `<span><b>${data.name}</b></span> - <i>${data.description}</i>`;

    html += `<span class='float-right'><small>{% trans "Company ID" %}: ${data.pk}</small></span>`;

    return html;
}


// Renderer for "StockItem" model
// eslint-disable-next-line no-unused-vars
function renderStockItem(name, data, parameters, options) {

    var image = blankImage();
    
    if (data.part_detail) {
        image = data.part_detail.thumbnail || data.part_detail.image || blankImage();
    }

    var html = '';
    
    var render_part_detail = true;

    if ('render_part_detail' in parameters) {
        render_part_detail = parameters['render_part_detail'];
    }

    if (render_part_detail) {
        html += `<img src='${image}' class='select2-thumbnail'>`;
        html += ` <span>${data.part_detail.full_name || data.part_detail.name}</span>`;
    }

    html += '<span>';

    if (data.serial && data.quantity == 1) {
        html += `{% trans "Serial Number" %}: ${data.serial}`;
    } else {
        html += `{% trans "Quantity" %}: ${data.quantity}`;
    }

    html += '</span>';

    if (render_part_detail && data.part_detail.description) {
        html += `<p><small>${data.part_detail.description}</small></p>`;
    }

    var render_stock_id = true;

    if ('render_stock_id' in parameters) {
        render_stock_id = parameters['render_stock_id'];
    }

    if (render_stock_id) {
        html += `<span class='float-right'><small>{% trans "Stock ID" %}: ${data.pk}</small></span>`;
    }

    var render_location_detail = false;

    if ('render_location_detail' in parameters) {
        render_location_detail = parameters['render_location_detail'];
    }

    if (render_location_detail && data.location_detail) {
        html += `<span> - ${data.location_detail.name}</span>`;
    }

    return html;
}


// Renderer for "StockLocation" model
// eslint-disable-next-line no-unused-vars
function renderStockLocation(name, data, parameters, options) {

    var level = '- '.repeat(data.level);

    var html = `<span>${level}${data.pathstring}</span>`;

    var render_description = true;

    if ('render_description' in parameters) {
        render_description = parameters['render_description'];
    }

    if (render_description && data.description) {
        html += ` - <i>${data.description}</i>`;
    }

    html += `<span class='float-right'><small>{% trans "Location ID" %}: ${data.pk}</small></span>`;

    return html;
}

// eslint-disable-next-line no-unused-vars
function renderBuild(name, data, parameters, options) {
    
    var image = null;

    if (data.part_detail && data.part_detail.thumbnail) {
        image = data.part_detail.thumbnail;
    } 

    var html = select2Thumbnail(image);

    html += `<span><b>${data.reference}</b></span> - ${data.quantity} x ${data.part_detail.full_name}`;
    html += `<span class='float-right'><small>{% trans "Build ID" %}: ${data.pk}</span></span>`;

    html += `<p><i>${data.title}</i></p>`;

    return html;
}


// Renderer for "Part" model
// eslint-disable-next-line no-unused-vars
function renderPart(name, data, parameters, options) {

    var html = select2Thumbnail(data.image);
    
    html += ` <span>${data.full_name || data.name}</span>`;

    if (data.description) {
        html += ` - <i>${data.description}</i>`;
    }

    html += `<span class='float-right'><small>{% trans "Part ID" %}: ${data.pk}</small></span>`;

    return html;
}

// Renderer for "User" model
// eslint-disable-next-line no-unused-vars
function renderUser(name, data, parameters, options) {

    var html = `<span>${data.username}</span>`;

    if (data.first_name && data.last_name) {
        html += ` - <i>${data.first_name} ${data.last_name}</i>`;
    }

    return html;
}


// Renderer for "Owner" model
// eslint-disable-next-line no-unused-vars
function renderOwner(name, data, parameters, options) {

    var html = `<span>${data.name}</span>`;

    switch (data.label) {
    case 'user':
        html += `<span class='float-right fas fa-user'></span>`;
        break;
    case 'group':
        html += `<span class='float-right fas fa-users'></span>`;
        break;
    default:
        break;
    }

    return html;
}


// Renderer for "PartCategory" model
// eslint-disable-next-line no-unused-vars
function renderPartCategory(name, data, parameters, options) {

    var level = '- '.repeat(data.level);

    var html = `<span>${level}${data.pathstring}</span>`;

    if (data.description) {
        html += ` - <i>${data.description}</i>`;
    }

    html += `<span class='float-right'><small>{% trans "Category ID" %}: ${data.pk}</small></span>`;

    return html;
}

// eslint-disable-next-line no-unused-vars
function renderPartParameterTemplate(name, data, parameters, options) {

    var html = `<span>${data.name} - [${data.units}]</span>`;

    return html;
}


// Renderer for "ManufacturerPart" model
// eslint-disable-next-line no-unused-vars
function renderManufacturerPart(name, data, parameters, options) {

    var manufacturer_image = null;
    var part_image = null;

    if (data.manufacturer_detail) {
        manufacturer_image = data.manufacturer_detail.image;
    }

    if (data.part_detail) {
        part_image = data.part_detail.thumbnail || data.part_detail.image;
    }

    var html = '';

    html += select2Thumbnail(manufacturer_image);
    html += select2Thumbnail(part_image);

    html += ` <span><b>${data.manufacturer_detail.name}</b> - ${data.MPN}</span>`;
    html += ` - <i>${data.part_detail.full_name}</i>`;

    html += `<span class='float-right'><small>{% trans "Manufacturer Part ID" %}: ${data.pk}</small></span>`;

    return html;
}


// Renderer for "SupplierPart" model
// eslint-disable-next-line no-unused-vars
function renderSupplierPart(name, data, parameters, options) {

    var supplier_image = null;
    var part_image = null;
    
    if (data.supplier_detail) {
        supplier_image = data.supplier_detail.image;
    }

    if (data.part_detail) {
        part_image = data.part_detail.thumbnail || data.part_detail.image;
    }

    var html = '';
    
    html += select2Thumbnail(supplier_image);
    html += select2Thumbnail(part_image);
    
    html += ` <span><b>${data.supplier_detail.name}</b> - ${data.SKU}</span>`;
    html += ` - <i>${data.part_detail.full_name}</i>`;

    html += `<span class='float-right'><small>{% trans "Supplier Part ID" %}: ${data.pk}</small></span>`;


    return html;

}
