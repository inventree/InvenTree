{% load i18n %}

/* globals
    blankImage,
    partStockLabel,
    renderLink,
    select2Thumbnail
    shortenString,
    user_settings
*/

/* exported
    getModelRenderer,
    renderBuild,
    renderCompany,
    renderContact,
    renderAddress,
    renderGroup,
    renderManufacturerPart,
    renderOwner,
    renderPart,
    renderPartCategory,
    renderProjectCode,
    renderReturnOrder,
    renderStockItem,
    renderStockLocation,
    renderStockLocationType,
    renderSupplierPart,
    renderUser,
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


/*
 * Return an appropriate model renderer based on the 'name' of the model
 */
function getModelRenderer(model) {

    // Find a custom renderer
    switch (model) {
    case 'company':
        return renderCompany;
    case 'contact':
        return renderContact;
    case 'address':
        return renderAddress;
    case 'stockitem':
        return renderStockItem;
    case 'stocklocation':
        return renderStockLocation;
    case 'stocklocationtype':
        return renderStockLocationType;
    case 'part':
        return renderPart;
    case 'partcategory':
        return renderPartCategory;
    case 'partparametertemplate':
        return renderPartParameterTemplate;
    case 'parttesttemplate':
        return renderPartTestTemplate;
    case 'purchaseorder':
        return renderPurchaseOrder;
    case 'salesorder':
        return renderSalesOrder;
    case 'returnorder':
        return renderReturnOrder;
    case 'salesordershipment':
        return renderSalesOrderShipment;
    case 'manufacturerpart':
        return renderManufacturerPart;
    case 'supplierpart':
        return renderSupplierPart;
    case 'build':
        return renderBuild;
    case 'owner':
        return renderOwner;
    case 'user':
        return renderUser;
    case 'group':
        return renderGroup;
    case 'projectcode':
        return renderProjectCode;
    default:
        // Un-handled model type
        console.error(`Rendering not implemented for model '${model}'`);
        return null;
    }
}


/*
 * Generic method for rendering model data in a consistent fashion:
 *
 * data:
 *  - image: Render an image (optional)
 *  - imageSecondary: Render a secondary image (optional)
 *  - text: Primary text
 *  - pk: primary key (unique ID) of the model instance
 *  - textSecondary: Secondary text
 *  - url: href for link target (is enabled or disabled by showLink option)
 *  - labels: extra labels to display
 *
 * options:
 *  - showImage: Option to create image(s) (default = true)
 *  - showLink: Option to create link (default = false)
 *  - showLabels: Option to show or hide extra labels (default = true)
 */
function renderModel(data, options={}) {

    let showImage = ('showImage' in options) ? options.showImage : true;
    let showLink = ('showLink' in options) ? options.showLink : false;
    let showLabels = ('showLabels' in options) ? options.showLabels : true;

    let html = '';

    if (showImage) {
        if (data.image) {
            html += select2Thumbnail(data.image);
        }
        if (data.imageSecondary) {
            html += select2Thumbnail(data.imageSecondary);
        }
    }

    let text = data.text;

    if (showLink && data.url) {
        text = renderLink(text, data.url);
    }

    text = `<span>${text}</span>`;

    if (data.textSecondary) {
        text += ` - <small><em>${data.textSecondary}</em></small>`;
    }



    html += text;

    if (showLabels && data.labels) {
        html += `<span class='float-right'><small>${data.labels}</small></span>`;
    }

    return html;

}


// Renderer for "Company" model
function renderCompany(data, parameters={}) {

    return renderModel(
        {
            image: data.image || blankImage(),
            text: data.name,
            textSecondary: shortenString(data.description),
            url: data.url || `/company/${data.pk}/`,
        },
        parameters
    );
}


// Renderer for "Contact" model
function renderContact(data, parameters={}) {
    return renderModel(
        {
            text: data.name,
        },
        parameters
    );
}


// Renderer for "Address" model
function renderAddress(data, parameters={}) {
    return renderModel(
        {
            text: [data.title, data.country, data.postal_code, data.postal_city, data.province, data.line1, data.line2].filter(Boolean).join(', '),
        },
        parameters
    );
}


// Renderer for "StockItem" model
function renderStockItem(data, parameters={}) {

    let part_image = null;
    let render_part_detail = ('render_part_detail' in parameters) ? parameters.render_part_detail : true;
    let render_location_detail = ('render_location_detail' in parameters) ? parameters.render_location_detail : false;
    let render_available_quantity = ('render_available_quantity' in parameters) ? parameters.render_available_quantity : false;

    let text = '';
    let stock_detail = '';

    if (render_part_detail && data.part_detail) {
        part_image = data.part_detail.thumbnail || data.part_detail.image || blankImage();

        text += data.part_detail.full_name;
    }

    if (render_location_detail && data.location_detail) {
        text += ` <small>- (<em>${data.location_detail.name}</em>)</small>`;
    }

    if (data.quantity == 0) {
        stock_detail = `<span class='badge rounded-pill bg-danger'>{% trans "No Stock"% }</span>`;
    } else {
        if (data.serial && data.quantity == 1) {
            stock_detail = `{% trans "Serial Number" %}: ${data.serial}`;
        } else {
            if (render_available_quantity) {
                var available = data.quantity - data.allocated;
                stock_detail = `{% trans "Available" %}: ${available}`;
            } else {
                stock_detail = `{% trans "Quantity" %}: ${data.quantity}`;
            }
        }

        if (data.batch) {
            stock_detail += ` - <small>{% trans "Batch" %}: ${data.batch}</small>`;
        }
    }

    return renderModel(
        {
            image: part_image,
            text: text,
            textSecondary: stock_detail,
            url: data.url || `/stock/item/${data.pk}/`,
        },
        parameters
    );
}


// Renderer for "StockLocation" model
function renderStockLocation(data, parameters={}) {

    let render_description = ('render_description' in parameters) ? parameters.render_description : true;
    let level = '- '.repeat(data.level);

    return renderModel(
        {
            text: `${level}${data.pathstring}`,
            textSecondary: render_description ? shortenString(data.description) : '',
            url: data.url || `/stock/location/${data.pk}/`,
        },
        parameters
    );
}

// Renderer for "StockLocationType" model
function renderStockLocationType(data, parameters={}) {
    return renderModel(
        {
            text: `<span class="${data.icon} me-1"></span>${data.name}`,
        },
        parameters
    );
}

function renderBuild(data, parameters={}) {

    var image = blankImage();

    if (data.part_detail && data.part_detail.thumbnail) {
        image = data.part_detail.thumbnail || data.part_detail.image || blankImage();
    }

    return renderModel(
        {
            image: image,
            text: data.reference,
            textSecondary: `${data.quantity} x ${data.part_detail.full_name}`,
            url: data.url || `/build/${data.pk}/`,
        },
        parameters
    );
}


// Renderer for "Part" model
function renderPart(data, parameters={}) {

    let labels = '';

    if (user_settings.PART_SHOW_QUANTITY_IN_FORMS) {
        labels = partStockLabel(data);

        if (!data.active) {
            labels += `<span class='badge badge-right rounded-pill bg-danger'>{% trans "Inactive" %}</span>`;
        }
    }

    return renderModel(
        {
            image: data.image || blankImage(),
            text: data.full_name || data.name,
            textSecondary: shortenString(data.description),
            labels: labels,
            url: data.url || `/part/${data.pk}/`,
        },
        parameters,
    );
}


// Renderer for "Group" model
function renderGroup(data, parameters={}) {

    return renderModel(
        {
            text: data.name,
        },
        parameters
    );
}

// Renderer for "User" model
function renderUser(data, parameters={}) {

    return renderModel(
        {
            text: data.username,
            textSecondary: `${data.first_name} ${data.last_name}`,
        },
        parameters
    );
}


// Renderer for "Owner" model
function renderOwner(data, parameters={}) {

    let label = '';

    switch (data.label) {
    case 'user':
        label = `<span class='float-right fas fa-user'></span>`;
        break;
    case 'group':
        label = `<span class='float-right fas fa-users'></span>`;
        break;
    default:
        break;
    }

    return renderModel(
        {
            text: data.name,
            labels: label,
        },
        parameters
    );

}


// Renderer for "PurchaseOrder" model
function renderPurchaseOrder(data, parameters={}) {

    let image = blankImage();

    if (data.supplier_detail) {
        image = data.supplier_detail.thumbnail || data.supplier_detail.image || blankImage();
    }

    return renderModel(
        {
            image: image,
            text: `${data.reference} - ${data.supplier_detail.name}`,
            textSecondary: shortenString(data.description),
            url: data.url || `/order/purchase-order/${data.pk}/`,
        },
        parameters
    );
}


// Renderer for "SalesOrder" model
function renderSalesOrder(data, parameters={}) {

    let image = blankImage();

    if (data.customer_detail) {
        image = data.customer_detail.thumbnail || data.customer_detail.image || blankImage();
    }

    let text = data.reference;

    if (data.customer_detail) {
        text += ` - ${data.customer_detail.name}`;
    }

    return renderModel(
        {
            image: image,
            text: text,
            textSecondary: shortenString(data.description),
            url: data.url || `/order/sales-order/${data.pk}/`,
        },
        parameters
    );
}


// Renderer for "ReturnOrder" model
function renderReturnOrder(data, parameters={}) {
    let image = blankImage();

    if (data.customer_detail) {
        image = data.customer_detail.thumbnail || data.customer_detail.image || blankImage();
    }

    return renderModel(
        {
            image: image,
            text: `${data.reference} - ${data.customer_detail.name}`,
            textSecondary: shortenString(data.description),
            url: data.url || `/order/return-order/${data.pk}/`,
        },
        parameters,
    );
}


// Renderer for "SalesOrderShipment" model
function renderSalesOrderShipment(data, parameters={}) {

    return renderModel(
        {
            text: data.order_detail.reference,
            textSecondary: `{% trans "Shipment" %} ${data.reference}`,
        },
        parameters
    );
}


// Renderer for "PartCategory" model
function renderPartCategory(data, parameters={}) {

    let level = '- '.repeat(data.level);

    return renderModel(
        {
            text: `${level}${data.pathstring}`,
            textSecondary: shortenString(data.description),
            url: data.url || `/part/category/${data.pk}/`,
        },
        parameters
    );
}


function renderPartParameterTemplate(data, parameters={}) {

    let units = '';

    if (data.units) {
        units = ` [${data.units}]`;
    }

    return renderModel(
        {
            text: `${data.name}${units}`,
        },
        parameters
    );
}


function renderPartTestTemplate(data, parameters={}) {

    return renderModel(
        {
            text: data.test_name,
            textSecondary: data.description,
        },
        parameters
    );
}


// Renderer for "ManufacturerPart" model
function renderManufacturerPart(data, parameters={}) {

    return renderModel(
        {
            image: data.manufacturer_detail ? data.manufacturer_detail.thumbnail || data.manufacturer_detail.image || blankImage() : null,
            imageSecondary: data.part.detail ? data.part_detail.thumbnail || data.part_detail.image || blankImage() : null,
            text: `${data.manufacturer_detail.name} - ${data.MPN}`,
            textSecondary: data.part_detail.full_name,
            url: data.url || `/manufacturer-part/${data.pk}/`,
        },
        parameters
    );
}


// Renderer for "SupplierPart" model
function renderSupplierPart(data, parameters={}) {

    return renderModel(
        {
            image: data.supplier_detail ? data.supplier_detail.thumbnail || data.supplier_detail.image || blankImage() : null,
            imageSecondary: data.part_detail ? data.part_detail.thumbnail || data.part_detail.image || blankImage() : null,
            text: `${data.supplier_detail.name} - ${data.SKU}`,
            textSecondary: data.part_detail.full_name,
            url: data.url || `/supplier-part/${data.pk}/`
        },
        parameters
    );
}


// Renderer for "ProjectCode" model
function renderProjectCode(data, parameters={}) {

    return renderModel(
        {
            text: data.code,
            textSecondary: data.description,
        },
        parameters
    );
}
