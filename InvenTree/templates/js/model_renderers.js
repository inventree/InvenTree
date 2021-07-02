{% load i18n %}

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
function renderCompany(name, data, parameters, options) {

    var html = `<span>${data.name}</span> - <i>${data.description}</i>`;

    html += `<span class='float-right'>{% trans "Company ID" %}: ${data.pk}</span>`;

    return html;
}


// Renderer for "StockItem" model
function renderStockItem(name, data, parameters, options) {

    var image = data.part_detail.thumbnail || data.part_detail.image;

    if (!image) {
        image = `/static/img/blank_image.png`;
    }

    var html = `<img src='${image}' class='select2-thumbnail'>`;

    html += ` <span>${data.part_detail.full_name || data.part_detail.name}</span>`;

    if (data.serial && data.quantity == 1) {
        html += ` - <i>{% trans "Serial Number" %}: ${data.serial}`;
    } else {
        html += ` - <i>{% trans "Quantity" %}: ${data.quantity}`;
    }

    if (data.part_detail.description) {
        html += `<p><small>${data.part_detail.description}</small></p>`;
    }

    return html;
}


// Renderer for "StockLocation" model
function renderStockLocation(name, data, parameters, options) {

    var html = `<span>${data.name}</span>`;

    if (data.description) {
        html += ` - <i>${data.description}</i>`;
    }

    html += `<span class='float-right'>{% trans "Location ID" %}: ${data.pk}</span>`;

    if (data.pathstring) {
        html += `<p><small>${data.pathstring}</small></p>`;
    }

    return html;
}


// Renderer for "Part" model
function renderPart(name, data, parameters, options) {

    var image = data.image;

    if (!image) {
        image = `/static/img/blank_image.png`;
    }

    var html = `<img src='${image}' class='select2-thumbnail'>`;
    
    html += ` <span>${data.full_name || data.name}</span>`;

    if (data.description) {
        html += ` - <i>${data.description}</i>`;
    }

    html += `<span class='float-right'>{% trans "Part ID" %}: ${data.pk}</span>`;

    return html;
}


// Renderer for "PartCategory" model
function renderPartCategory(name, data, parameters, options) {

    var html = `<span><b>${data.name}</b></span>`;

    if (data.description) {
        html += ` - <i>${data.description}</i>`;
    }

    html += `<span class='float-right'>{% trans "Category ID" %}: ${data.pk}</span>`;

    if (data.pathstring) {
        html += `<p><small>${data.pathstring}</small></p>`;
    }

    return html;
}


// Rendered for "SupplierPart" model
function renderSupplierPart(name, data, parameters, options) {

    var image = data.supplier_detail.image;

    if (!image) {
        image = `/static/img/blank_image.png`;
    }

    var html = `<img src='${image}' class='select2-thumbnail'>`;
    
    html += ` <span><b>${data.supplier_detail.name}</b> - ${data.SKU}</span>`;

    html += `<span class='float-right'>{% trans "Supplier Part ID" %}: ${data.pk}</span>`;

    return html;

}