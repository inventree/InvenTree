{% load js_i18n %}

/* globals
    blankImage,
    select2Thumbnail
*/

/* exported
    renderBuild,
    renderCompany,
    renderManufacturerPart,
    renderOwner,
    renderPart,
    renderPartCategory,
    renderStockItem,
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


// Should the ID be rendered for this string
function renderId(title, pk, parameters={}) {

    // Default = do not render
    var render = false;

    if ('render_pk' in parameters) {
        render = parameters['render_pk'];
    }

    if (render) {
        return `<span class='float-right'><small>${title}: ${pk}</small></span>`;
    } else {
        return '';
    }
}


// Renderer for "Company" model
// eslint-disable-next-line no-unused-vars
function renderCompany(name, data, parameters={}, options={}) {

    var html = select2Thumbnail(data.image);

    html += `<span><b>${data.name}</b></span> - <i>${data.description}</i>`;

    html += renderId('{% trans "Company ID" %}', data.pk, parameters);

    return html;
}


// Renderer for "StockItem" model
// eslint-disable-next-line no-unused-vars
function renderStockItem(name, data, parameters={}, options={}) {

    var image = blankImage();

    if (data.part_detail) {
        image = data.part_detail.thumbnail || data.part_detail.image || blankImage();
    }

    var render_part_detail = true;

    if ('render_part_detail' in parameters) {
        render_part_detail = parameters['render_part_detail'];
    }

    var part_detail = '';

    if (render_part_detail && data.part_detail) {
        part_detail = `<img src='${image}' class='select2-thumbnail'><span>${data.part_detail.full_name}</span> - `;
    }

    var render_location_detail = false;

    if ('render_location_detail' in parameters) {
        render_location_detail = parameters['render_location_detail'];
    }

    var location_detail = '';

    if (render_location_detail && data.location_detail) {
        location_detail = ` <small>- (<em>${data.location_detail.name}</em>)</small>`;
    }

    var stock_detail = '';

    if (data.quantity == 0) {
        stock_detail = `<span class='badge rounded-pill bg-danger'>{% trans "No Stock"% }</span>`;
    } else {
        if (data.serial && data.quantity == 1) {
            stock_detail = `{% trans "Serial Number" %}: ${data.serial}`;
        } else {
            stock_detail = `{% trans "Quantity" %}: ${data.quantity}`;
        }

        if (data.batch) {
            stock_detail += ` - <small>{% trans "Batch" %}: ${data.batch}</small>`;
        }
    }

    var html = `
    <span>
        ${part_detail}
        ${stock_detail}
        ${location_detail}
        ${renderId('{% trans "Stock ID" %}', data.pk, parameters)}
    </span>
    `;

    return html;
}


// Renderer for "StockLocation" model
// eslint-disable-next-line no-unused-vars
function renderStockLocation(name, data, parameters={}, options={}) {

    var level = '- '.repeat(data.level);

    var html = `<span>${level}${data.pathstring}</span>`;

    var render_description = true;

    if ('render_description' in parameters) {
        render_description = parameters['render_description'];
    }

    if (render_description && data.description) {
        html += ` - <i>${data.description}</i>`;
    }

    html += renderId('{% trans "Location ID" %}', data.pk, parameters);

    return html;
}

// eslint-disable-next-line no-unused-vars
function renderBuild(name, data, parameters={}, options={}) {

    var image = null;

    if (data.part_detail && data.part_detail.thumbnail) {
        image = data.part_detail.thumbnail;
    }

    var html = select2Thumbnail(image);

    html += `<span><b>${data.reference}</b> - ${data.quantity} x ${data.part_detail.full_name}</span>`;

    html += renderId('{% trans "Build ID" %}', data.pk, parameters);

    return html;
}


// Renderer for "Part" model
// eslint-disable-next-line no-unused-vars
function renderPart(name, data, parameters={}, options={}) {

    var html = select2Thumbnail(data.image);

    html += ` <span>${data.full_name || data.name}</span>`;

    if (data.description) {
        html += ` - <i><small>${data.description}</small></i>`;
    }

    var stock_data = '';

    if (user_settings.PART_SHOW_QUANTITY_IN_FORMS) {
        stock_data = partStockLabel(data);
    }

    var extra = '';

    if (!data.active) {
        extra += `<span class='badge badge-right rounded-pill bg-danger'>{% trans "Inactive" %}</span>`;
    }

    html += `
    <span class='float-right'>
        <small>
            ${stock_data}
            ${extra}
            ${renderId('{% trans "Part ID" %}', data.pk, parameters)}
            </small>
    </span>`;

    return html;
}

// Renderer for "User" model
// eslint-disable-next-line no-unused-vars
function renderUser(name, data, parameters={}, options={}) {

    var html = `<span>${data.username}</span>`;

    if (data.first_name && data.last_name) {
        html += ` - <i>${data.first_name} ${data.last_name}</i>`;
    }

    return html;
}


// Renderer for "Owner" model
// eslint-disable-next-line no-unused-vars
function renderOwner(name, data, parameters={}, options={}) {

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


// Renderer for "PurchaseOrder" model
// eslint-disable-next-line no-unused-vars
function renderPurchaseOrder(name, data, parameters={}, options={}) {

    var prefix = global_settings.PURCHASEORDER_REFERENCE_PREFIX;
    var html = `<span>${prefix}${data.reference}</span>`;

    var thumbnail = null;

    if (data.supplier_detail) {
        thumbnail = data.supplier_detail.thumbnail || data.supplier_detail.image;

        html += ' - ' + select2Thumbnail(thumbnail);
        html += `<span>${data.supplier_detail.name}</span>`;
    }

    if (data.description) {
        html += ` - <em>${data.description}</em>`;
    }

    html += renderId('{% trans "Order ID" %}', data.pk, parameters);

    return html;
}


// Renderer for "SalesOrder" model
// eslint-disable-next-line no-unused-vars
function renderSalesOrder(name, data, parameters={}, options={}) {

    var prefix = global_settings.SALESORDER_REFERENCE_PREFIX;
    var html = `<span>${prefix}${data.reference}</span>`;

    var thumbnail = null;

    if (data.customer_detail) {
        thumbnail = data.customer_detail.thumbnail || data.customer_detail.image;

        html += ' - ' + select2Thumbnail(thumbnail);
        html += `<span>${data.customer_detail.name}</span>`;
    }

    if (data.description) {
        html += ` - <em>${data.description}</em>`;
    }

    html += renderId('{% trans "Order ID" %}', data.pk, parameters);

    return html;
}


// Renderer for "SalesOrderShipment" model
// eslint-disable-next-line no-unused-vars
function renderSalesOrderShipment(name, data, parameters={}, options={}) {

    var so_prefix = global_settings.SALESORDER_REFERENCE_PREFIX;

    var html = `
    <span>${so_prefix}${data.order_detail.reference} - {% trans "Shipment" %} ${data.reference}</span>
    <span class='float-right'>
        <small>{% trans "Shipment ID" %}: ${data.pk}</small>
    </span>
    `;

    html += renderId('{% trans "Shipment ID" %}', data.pk, parameters);

    return html;
}


// Renderer for "PartCategory" model
// eslint-disable-next-line no-unused-vars
function renderPartCategory(name, data, parameters={}, options={}) {

    var level = '- '.repeat(data.level);

    var html = `<span>${level}${data.pathstring}</span>`;

    if (data.description) {
        html += ` - <i>${data.description}</i>`;
    }

    html += renderId('{% trans "Category ID" %}', data.pk, parameters);

    return html;
}

// eslint-disable-next-line no-unused-vars
function renderPartParameterTemplate(name, data, parameters={}, options={}) {

    var units = '';

    if (data.units) {
        units = ` [${data.units}]`;
    }

    var html = `<span>${data.name}${units}</span>`;

    return html;
}


// Renderer for "ManufacturerPart" model
// eslint-disable-next-line no-unused-vars
function renderManufacturerPart(name, data, parameters={}, options={}) {

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

    html += renderId('{% trans "Manufacturer Part ID" %}', data.pk, parameters);

    return html;
}


// Renderer for "SupplierPart" model
// eslint-disable-next-line no-unused-vars
function renderSupplierPart(name, data, parameters={}, options={}) {

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

    if (data.part_detail) {
        html += select2Thumbnail(part_image);
    }

    if (data.supplier_detail) {
        html += ` <span><b>${data.supplier_detail.name}</b> - ${data.SKU}</span>`;
    }

    if (data.part_detail) {
        html += ` - <i>${data.part_detail.full_name}</i>`;
    }

    html += renderId('{% trans "Supplier Part ID" %}', data.pk, parameters);

    return html;
}
