{% load i18n %}
{% load inventree_extras %}

/* globals
    baseCurrency,
    Chart,
    constructForm,
    constructFormBody,
    constructInput,
    convertCurrency,
    formatCurrency,
    formatDecimal,
    formatPriceRange,
    getCurrencyConversionRates,
    getFormFieldValue,
    getTableData,
    global_settings,
    guessFieldType,
    handleFormErrors,
    handleFormSuccess,
    imageHoverIcon,
    inventreeGet,
    inventreeLoad,
    inventreePut,
    inventreeSave,
    loadTableFilters,
    makeDeleteButton,
    makeEditButton,
    makeIconBadge,
    makeIconButton,
    moment,
    orderParts,
    purchaseOrderStatusDisplay,
    receivePurchaseOrderItems,
    renderClipboard,
    renderDate,
    renderLink,
    setFormGroupVisibility,
    setupFilterList,
    shortenString,
    showAlertDialog,
    showApiError,
    showMessage,
    showModalSpinner,
    thumbnailImage,
    trueFalseLabel,
    updateFieldValue,
    withTitle,
    wrapButtons,
    yesNoLabel,
*/

/* exported
    createPart,
    createPartCategory,
    deletePart,
    deletePartCategory,
    duplicateBom,
    duplicatePart,
    editCategory,
    editPart,
    generateStocktakeReport,
    loadParametricPartTable,
    loadPartCategoryTable,
    loadPartParameterTable,
    loadPartParameterTemplateTable,
    loadPartPurchaseOrderTable,
    loadPartTable,
    loadPartTestTemplateTable,
    loadPartSchedulingChart,
    loadPartStocktakeTable,
    loadPartVariantTable,
    loadRelatedPartsTable,
    loadSimplePartTable,
    partDetail,
    partStockLabel,
    partTestTemplateFields,
    toggleStar,
    validateBom,
*/

/* Part API functions
 * Requires api.js to be loaded first
 */

function partGroups() {

    return {
        attributes: {
            title: '{% trans "Part Attributes" %}',
            collapsible: true,
        },
        create: {
            title: '{% trans "Part Creation Options" %}',
            collapsible: true,
        },
        duplicate: {
            title: '{% trans "Part Duplication Options" %}',
            collapsible: true,
        },
        initial_stock: {
            title: '{% trans "Initial Stock" %}',
            collapsible: true,
            hidden: !global_settings.PART_CREATE_INITIAL,
        },
        initial_supplier: {
            title: '{% trans "Initial Supplier Data" %}',
            collapsible: true,
            hidden: !global_settings.PART_CREATE_SUPPLIER,
        },
    };
}


// Construct fieldset for part forms
function partFields(options={}) {

    var fields = {
        category: {
            secondary: {
                title: '{% trans "Add Part Category" %}',
                fields: function() {
                    var fields = categoryFields();

                    return fields;
                }
            },
            filters: {
                structural: false,
            },
            tree_picker: {
                url: '{% url "api-part-category-tree" %}',
                default_icon: global_settings.PART_CATEGORY_DEFAULT_ICON,
            },
        },
        name: {},
        IPN: {},
        revision: {
            icon: 'fa-code-branch',
        },
        description: {},
        variant_of: {},
        keywords: {
            icon: 'fa-key',
        },
        units: {},
        link: {
            icon: 'fa-link',
        },
        default_location: {
            icon: 'fa-sitemap',
            filters: {
                structural: false,
            },
            tree_picker: {
                url: '{% url "api-location-tree" %}',
                default_icon: global_settings.STOCK_LOCATION_DEFAULT_ICON,
            },
        },
        default_supplier: {
            icon: 'fa-building',
            filters: {
                part_detail: true,
                supplier_detail: true,
            }
        },
        default_expiry: {
            icon: 'fa-calendar-alt',
        },
        minimum_stock: {
            icon: 'fa-boxes',
        },
        responsible: {
            icon: 'fa-user',
            filters: {
                is_active: true,
            }
        },
        component: {
            default: global_settings.PART_COMPONENT,
            group: 'attributes',
        },
        assembly: {
            default: global_settings.PART_ASSEMBLY,
            group: 'attributes',
        },
        is_template: {
            default: global_settings.PART_TEMPLATE,
            group: 'attributes',
        },
        trackable: {
            default: global_settings.PART_TRACKABLE,
            group: 'attributes',
        },
        purchaseable: {
            default: global_settings.PART_PURCHASEABLE,
            group: 'attributes',
            onEdit: function(value, name, field, options) {
                setFormGroupVisibility('supplier', value, options);
            }
        },
        salable: {
            default: global_settings.PART_SALABLE,
            group: 'attributes',
        },
        virtual: {
            default: global_settings.PART_VIRTUAL,
            group: 'attributes',
        },
    };

    if (options.category) {
        fields.category.value = options.category;
    }

    // If editing a part, we can set the "active" status
    if (options.edit) {
        fields.active = {
            group: 'attributes'
        };
    }

    // Pop 'expiry' field
    if (!global_settings.STOCK_ENABLE_EXPIRY) {
        delete fields['default_expiry'];
    }

    // Pop 'revision' field
    if (!global_settings.PART_ENABLE_REVISION) {
        delete fields['revision'];
    }

    if (options.create || options.duplicate) {

        // Add fields for creating initial supplier data

        // Add fields for creating initial stock
        if (global_settings.PART_CREATE_INITIAL) {

            fields.initial_stock__quantity = {
                value: 0,
            };
            fields.initial_stock__location = {};
        }

        // Add fields for creating initial supplier data
        if (global_settings.PART_CREATE_SUPPLIER) {
            fields.initial_supplier__supplier = {
                filters: {
                    is_supplier: true,
                }
            };
            fields.initial_supplier__sku = {};
            fields.initial_supplier__manufacturer = {
                filters: {
                    is_manufacturer: true,
                }
            };
            fields.initial_supplier__mpn = {};
        }

        // No supplier parts available yet
        delete fields['default_supplier'];

        fields.copy_category_parameters = {
            value: global_settings.PART_CATEGORY_PARAMETERS,
            group: 'create',
        };
    }

    // Additional fields when "duplicating" a part
    if (options.duplicate) {

        // The following fields exist under the child serializer named 'duplicate'

        fields.duplicate__part = {
            value: options.duplicate,
            hidden: true,
        };

        fields.duplicate__copy_image = {
            value: true,
        };

        fields.duplicate__copy_bom = {
            value: global_settings.PART_COPY_BOM,
        };

        fields.duplicate__copy_notes = {
            value: true,
        }

        fields.duplicate__copy_parameters = {
            value: global_settings.PART_COPY_PARAMETERS,
        };
    }

    return fields;
}


/*
 * Construct a set of fields for a PartCategory instance
 */
function categoryFields(options={}) {
    let fields = {
        parent: {
            help_text: '{% trans "Parent part category" %}',
            required: false,
            tree_picker: {
                url: '{% url "api-part-category-tree" %}',
                default_icon: global_settings.PART_CATEGORY_DEFAULT_ICON,
            },
        },
        name: {},
        description: {},
        default_location: {
            icon: 'fa-sitemap',
            filters: {
                structural: false,
            },
            tree_picker: {
                url: '{% url "api-location-tree" %}',
                default_icon: global_settings.STOCK_LOCATION_DEFAULT_ICON,
            },
        },
        default_keywords: {
            icon: 'fa-key',
        },
        structural: {},
        icon: {
            help_text: `{% trans "Icon (optional) - Explore all available icons on" %} <a href="https://fontawesome.com/v5/search?s=solid" target="_blank" rel="noopener noreferrer">Font Awesome</a>.`,
            placeholder: 'fas fa-tag',
        },
    };

    if (options.parent) {
        fields.parent.value = options.parent;
    }

    return fields;
}


// Create a PartCategory via the API
function createPartCategory(options={}) {
    let fields = categoryFields(options);

    constructForm('{% url "api-part-category-list" %}', {
        fields: fields,
        method: 'POST',
        title: '{% trans "Create Part Category" %}',
        follow: true,
        persist: true,
        persistMessage: '{% trans "Create new category after this one" %}',
        successMessage: '{% trans "Part category created" %}'
    });
}


// Edit a PartCategory via the API
function editCategory(pk) {

    var url = `/api/part/category/${pk}/`;

    var fields = categoryFields();

    constructForm(url, {
        fields: fields,
        title: '{% trans "Edit Part Category" %}',
        reload: true,
    });
}

/*
 * Delete a PartCategory via the API
 */
function deletePartCategory(pk, options={}) {
    var url = `/api/part/category/${pk}/`;

    var html = `
    <div class='alert alert-block alert-danger'>
    {% trans "Are you sure you want to delete this part category?" %}
    </div>`;
    var subChoices = [
        {
            value: 0,
            display_name: '{% trans "Move to parent category" %}',
        },
        {
            value: 1,
            display_name: '{% trans "Delete" %}',
        }
    ];

    constructForm(url, {
        title: '{% trans "Delete Part Category" %}',
        method: 'DELETE',
        fields: {
            'delete_parts': {
                label: '{% trans "Action for parts in this category" %}',
                choices: subChoices,
                type: 'choice'
            },
            'delete_child_categories': {
                label: '{% trans "Action for child categories" %}',
                choices: subChoices,
                type: 'choice'
            },
        },
        preFormContent: html,
        onSuccess: function(response) {
            handleFormSuccess(response, options);
        }
    });
}


/*
 * Launches a form to create a new Part instance
 */
function createPart(options={}) {

    options.create = true;

    constructForm('{% url "api-part-list" %}', {
        method: 'POST',
        fields: partFields(options),
        groups: partGroups(),
        title: '{% trans "Create Part" %}',
        persist: true,
        persistMessage: '{% trans "Create another part after this one" %}',
        successMessage: '{% trans "Part created successfully" %}',
        onSuccess: function(data) {
            // Follow the new part
            location.href = `/part/${data.pk}/`;
        },
    });
}


/*
 * Launches a form to edit an existing Part instance
 */
function editPart(pk) {

    var url = `{% url "api-part-list" %}${pk}/`;

    var fields = partFields({
        edit: true
    });

    // Filter supplied parts by the Part ID
    fields.default_supplier.filters.part = pk;

    var groups = partGroups({});

    constructForm(url, {
        fields: fields,
        groups: groups,
        title: '{% trans "Edit Part" %}',
        reload: true,
        successMessage: '{% trans "Part edited" %}',
    });
}


// Launch form to duplicate a part
function duplicatePart(pk, options={}) {

    var title = '{% trans "Duplicate Part" %}';

    if (options.variant) {
        title = '{% trans "Create Part Variant" %}';
    }

    // First we need all the part information
    inventreeGet(`{% url "api-part-list" %}${pk}/`, {}, {

        success: function(data) {

            var fields = partFields({
                duplicate: pk,
            });

            if (fields.initial_stock_location) {
                fields.initial_stock_location.value = data.default_location;
            }

            // Remove "default_supplier" field
            delete fields['default_supplier'];

            // If we are making a "variant" part
            if (options.variant) {

                // Override the "variant_of" field
                data.variant_of = pk;

                // By default, disable "is_template" when making a variant *of* a template
                data.is_template = false;
            }

            // Clear IPN field if PART_ALLOW_DUPLICATE_IPN is set to False
            if (!global_settings['PART_ALLOW_DUPLICATE_IPN']) {
                data.IPN = '';
            }

            constructForm('{% url "api-part-list" %}', {
                method: 'POST',
                fields: fields,
                groups: partGroups(),
                title: title,
                data: data,
                onSuccess: function(data) {
                    // Follow the new part
                    location.href = `/part/${data.pk}/`;
                }
            });
        }
    });
}


// Launch form to delete a part
function deletePart(pk, options={}) {

    inventreeGet(`{% url "api-part-list" %}${pk}/`, {}, {
        success: function(part) {
            if (part.active) {
                showAlertDialog(
                    '{% trans "Active Part" %}',
                    '{% trans "Part cannot be deleted as it is currently active" %}',
                    {
                        alert_style: 'danger',
                    }
                );
                return;
            }

            var thumb = thumbnailImage(part.thumbnail || part.image);

            var html = `
            <div class='alert alert-block alert-danger'>
            <p>${thumb} ${part.full_name} - <em>${part.description}</em></p>

            {% trans "Deleting this part cannot be reversed" %}
            <ul>
            <li>{% trans "Any stock items for this part will be deleted" %}</li>
            <li>{% trans "This part will be removed from any Bills of Material" %}</li>
            <li>{% trans "All manufacturer and supplier information for this part will be deleted" %}</li>
            </div>`;

            constructForm(
                `{% url "api-part-list" %}${pk}/`,
                {
                    method: 'DELETE',
                    title: '{% trans "Delete Part" %}',
                    preFormContent: html,
                    onSuccess: function(response) {
                        handleFormSuccess(response, options);
                    }
                }
            );
        }
    });
}

/* Toggle the 'starred' status of a part.
 * Performs AJAX queries and updates the display on the button.
 *
 * options:
 * - button: ID of the button (default = '#part-star-icon')
 * - URL: API url of the object
 * - user: pk of the user
 */
function toggleStar(options) {

    inventreeGet(options.url, {}, {
        success: function(response) {

            var starred = response.starred;

            inventreePut(
                options.url,
                {
                    starred: !starred,
                },
                {
                    method: 'PATCH',
                    success: function(response) {
                        if (response.starred) {
                            $(options.button).removeClass('fa fa-bell-slash').addClass('fas fa-bell icon-green');
                            $(options.button).attr('title', '{% trans "You are subscribed to notifications for this item" %}');

                            showMessage('{% trans "You have subscribed to notifications for this item" %}', {
                                style: 'success',
                            });
                        } else {
                            $(options.button).removeClass('fas fa-bell icon-green').addClass('fa fa-bell-slash');
                            $(options.button).attr('title', '{% trans "Subscribe to notifications for this item" %}');

                            showMessage('{% trans "You have unsubscribed to notifications for this item" %}', {
                                style: 'warning',
                            });
                        }
                    }
                }
            );
        }
    });
}


/* Validate a BOM */
function validateBom(part_id, options={}) {

    var html = `
    <div class='alert alert-block alert-success'>
    {% trans "Validating the BOM will mark each line item as valid" %}
    </div>
    `;

    constructForm(`{% url "api-part-list" %}${part_id}/bom-validate/`, {
        method: 'PUT',
        fields: {
            valid: {},
        },
        preFormContent: html,
        title: '{% trans "Validate Bill of Materials" %}',
        reload: options.reload,
        onSuccess: function(response) {
            showMessage('{% trans "Validated Bill of Materials" %}');
        }
    });
}


/* Duplicate a BOM */
function duplicateBom(part_id, options={}) {

    constructForm(`{% url "api-part-list" %}${part_id}/bom-copy/`, {
        method: 'POST',
        fields: {
            part: {
                icon: 'fa-shapes',
                filters: {
                    assembly: true,
                    exclude_tree: part_id,
                }
            },
            include_inherited: {},
            copy_substitutes: {},
            remove_existing: {},
            skip_invalid: {},
        },
        confirm: true,
        title: '{% trans "Copy Bill of Materials" %}',
        onSuccess: function(response) {
            if (options.success) {
                options.success(response);
            }
        },
    });

}


/*
 * Construct a "badge" label showing stock information for this particular part
 */
function partStockLabel(part, options={}) {
    var classes = options.classes || '';

    // Prevent literal string 'null' from being displayed
    var units = part.units || '';

    let elements = [];

    // Check for stock
    if (part.total_in_stock) {
        // There IS stock available for this part

        // Is stock "low" (below the 'minimum_stock' quantity)?
        if ((part.minimum_stock > 0) && (part.minimum_stock > part.total_in_stock)) {
            elements.push(`{% trans "Low stock" %}: ${part.total_in_stock}`);
        } else if (part.unallocated_stock <= 0) {
            // There is no available stock at all
            elements.push(`{% trans "No stock available" %}`);
        } else if (part.unallocated_stock < part.in_stock) {
            // Unallocated quantity is less than total quantity
            if (options.hideTotalStock) {
                elements.push(`{% trans "Available" %}: ${part.unallocated_stock}`);
            } else {
                elements.push(`{% trans "Available" %}: ${part.unallocated_stock}/${part.in_stock}`);
            }
        } else {
            // Stock is completely available
            if (!options.hideTotalStock) {
                elements.push(`{% trans "Available" %}: ${part.unallocated_stock}`);
            }
        }
    } else {
        // There IS NO stock available for this part
        elements.push(`{% trans "No Stock" %}`);
    }

    // Check for items on order
    if (part.ordering) {
        elements.push(`{% trans "On Order" %}: ${part.ordering}`);
    }

    // Check for items being built
    if (part.building) {
        elements.push(`{% trans "Building" %}: ${part.building}`);
    }

    // Determine badge color based on overall stock health
    var stock_health = part.unallocated_stock + part.building + part.ordering - part.minimum_stock;

    // TODO: Refactor the API to include this information, so we don't have to request it!
    if (options.showDemandInfo) {

        // Check for demand from unallocated build orders
        var required_build_order_quantity = null;
        var required_sales_order_quantity = null;

        inventreeGet(`{% url "api-part-list" %}${part.pk}/requirements/`, {}, {
            async: false,
            success: function(response) {
                required_build_order_quantity = 0;
                if (response.required_build_order_quantity) {
                    required_build_order_quantity = response.required_build_order_quantity;
                }
                required_sales_order_quantity = 0;
                if (response.required_sales_order_quantity) {
                    required_sales_order_quantity = response.required_sales_order_quantity;
                }
            }
        });

        if ((required_build_order_quantity == null) || (required_sales_order_quantity == null)) {
            console.error(`Error loading part requirements for part ${part.pk}`);
            return;
        }

        var demand = (required_build_order_quantity - part.allocated_to_build_orders) + (required_sales_order_quantity - part.allocated_to_sales_orders);
        if (demand) {
            elements.push(`{% trans "Demand" %}: ${demand}`);
        }

        stock_health -= (required_build_order_quantity + required_sales_order_quantity);
    }

    var bg_class = '';

    if (stock_health < 0) {
        // Unsatisfied demand and/or below minimum stock
        bg_class = 'bg-danger';
    } else if (stock_health == 0) {
        // Demand and minimum stock matched exactly by available stock and incoming/building
        bg_class = 'bg-warning';
    } else {
        // Surplus stock available or already incoming/building in sufficient quantities
        bg_class = 'bg-success';
    }

    let output = '';

    // Display units next to stock badge
    if (units && !options.no_units) {
        output += `<span class='badge rounded-pill text-muted bg-muted ${classes}'>{% trans "Unit" %}: ${units}</span> `;
    }

    if (elements.length > 0) {
        let text = elements.join(' | ');
        output += `<span class='badge rounded-pill ${bg_class} ${classes}'>${text}</span>`;
    }

    return output;
}


function makePartIcons(part) {
    /* Render a set of icons for the given part.
     */

    var html = '';

    if (part.trackable) {
        html += makeIconBadge('fa-directions', '{% trans "Trackable part" %}');
    }

    if (part.virtual) {
        html += makeIconBadge('fa-ghost', '{% trans "Virtual part" %}');
    }

    if (part.is_template) {
        html += makeIconBadge('fa-clone', '{% trans "Template part" %}');
    }

    if (part.assembly) {
        html += makeIconBadge('fa-tools', '{% trans "Assembled part" %}');
    }

    if (part.starred) {
        html += makeIconBadge('fa-bell icon-green', '{% trans "Subscribed part" %}');
    }

    if (part.salable) {
        html += makeIconBadge('fa-dollar-sign', '{% trans "Salable part" %}');
    }

    if (!part.active) {
        html += `<span class='badge badge-right rounded-pill bg-warning'>{% trans "Inactive" %}</span> `;
    }

    return html;
}


/*
 * Render part information for a table view
 *
 * part: JSON part object
 * options:
 *  icons: Display part icons
 *  thumb: Display part thumbnail
 *  link: Display URL
 */
function partDetail(part, options={}) {

    var html = '';

    var name = part.full_name;

    if (options.thumb) {
        html += imageHoverIcon(part.thumbnail || part.image);
    }

    if (options.link) {
        var url = `/part/${part.pk}/`;
        html += renderLink(shortenString(name), url);
    } else {
        html += shortenString(name);
    }

    if (options.icons) {
        html += makePartIcons(part);
    }

    return html;
}


/*
 * Initiate generation of a stocktake report
 */
function generateStocktakeReport(options={}) {

    let fields = {
    };

    if (options.part != null) {
        fields.part = options.part;
    }

    if (options.category != null) {
        fields.category = options.category;
    }

    if (options.location != null) {
        fields.location = options.location;
    }

    fields.exclude_external = {
        value: global_settings.STOCKTAKE_EXCLUDE_EXTERNAL,
    };

    if (options.generate_report) {
        fields.generate_report = options.generate_report;
    }

    if (options.update_parts) {
        fields.update_parts = options.update_parts;
    }

    let content = `
    <div class='alert alert-block alert-info'>
    {% trans "Schedule generation of a new stocktake report." %} {% trans "Once complete, the stocktake report will be available for download." %}
    </div>
    `;

    constructForm(
        '{% url "api-part-stocktake-report-generate" %}',
        {
            method: 'POST',
            title: '{% trans "Generate Stocktake Report" %}',
            preFormContent: content,
            fields: fields,
            onSuccess: function(response) {
                showMessage('{% trans "Stocktake report scheduled" %}', {
                    style: 'success',
                });
            }
        }
    );
}

var stocktakeChart = null;

/*
 * Load chart to display part stocktake information
 */
function loadStocktakeChart(data, options={}) {

    var chart = 'part-stocktake-chart';
    var context = document.getElementById(chart);

    var quantity_data = [];
    var cost_min_data = [];
    var cost_max_data = [];

    var base_currency = baseCurrency();
    var rate_data = getCurrencyConversionRates();

    data.forEach(function(row) {
        var date = moment(row.date);
        quantity_data.push({
            x: date,
            y: row.quantity
        });

        if (row.cost_min) {
            cost_min_data.push({
                x: date,
                y: convertCurrency(
                    row.cost_min,
                    row.cost_min_currency || base_currency,
                    base_currency,
                    rate_data
                ),
            });
        }

        if (row.cost_max) {
            cost_max_data.push({
                x: date,
                y: convertCurrency(
                    row.cost_max,
                    row.cost_max_currency || base_currency,
                    base_currency,
                    rate_data
                ),
            });
        }
    });

    var chart_data = {
        datasets: [
            {
                label: '{% trans "Quantity" %}',
                data: quantity_data,
                backgroundColor: 'rgba(160, 80, 220, 0.75)',
                borderWidth: 3,
                borderColor: 'rgb(160, 80, 220)',
                yAxisID: 'y',
            },
            {
                label: '{% trans "Minimum Cost" %}',
                data: cost_min_data,
                backgroundColor: 'rgba(220, 160, 80, 0.25)',
                borderWidth: 2,
                borderColor: 'rgba(220, 160, 80, 0.35)',
                borderDash: [10, 5],
                yAxisID: 'y1',
                fill: '+1',
            },
            {
                label: '{% trans "Maximum Cost" %}',
                data: cost_max_data,
                backgroundColor: 'rgba(220, 160, 80, 0.25)',
                borderWidth: 2,
                borderColor: 'rgba(220, 160, 80, 0.35)',
                borderDash: [10, 5],
                yAxisID: 'y1',
                fill: '-1',
            }
        ]
    };

    if (stocktakeChart != null) {
        stocktakeChart.destroy();
    }

    stocktakeChart = new Chart(context, {
        type: 'scatter',
        data: chart_data,
        options: {
            showLine: true,
            scales: {
                x: {
                    type: 'time',
                    // suggestedMax: today.format(),
                    position: 'bottom',
                    time: {
                        minUnit: 'day',
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                }
            },
        }
    });
}



/*
 * Load table for part stocktake information
 */
function loadPartStocktakeTable(partId, options={}) {

    // HTML elements
    var table = options.table || '#part-stocktake-table';

    var params = options.params || {};

    params.part = partId;

    var filters = loadTableFilters('stocktake', params);

    setupFilterList('stocktake', $(table), '#filter-list-partstocktake');

    $(table).inventreeTable({
        url: '{% url "api-part-stocktake-list" %}',
        queryParams: filters,
        name: 'partstocktake',
        original: options.params,
        showColumns: true,
        sortable: true,
        formatNoMatches: function() {
            return '{% trans "No stocktake information available" %}';
        },
        onLoadSuccess: function(response) {
            var data = response.results || response;

            loadStocktakeChart(data);
        },
        columns: [
            {
                field: 'item_count',
                title: '{% trans "Stock Items" %}',
                switchable: true,
                sortable: true,
            },
            {
                field: 'quantity',
                title: '{% trans "Total Quantity" %}',
                switchable: false,
                sortable: true,
            },
            {
                field: 'cost',
                title: '{% trans "Total Cost" %}',
                switchable: false,
                formatter: function(value, row) {
                    return formatPriceRange(row.cost_min, row.cost_max);
                }
            },
            {
                field: 'note',
                title: '{% trans "Notes" %}',
                switchable: true,
            },
            {
                field: 'date',
                title: '{% trans "Date" %}',
                switchable: false,
                sortable: true,
                formatter: function(value, row) {
                    var html = renderDate(value);

                    if (row.user_detail) {
                        html += `<span class='badge bg-dark rounded-pill float-right'>${row.user_detail.username}</span>`;
                    }

                    return html;
                }
            },
            {
                field: 'actions',
                title: '',
                visible: options.allow_edit || options.allow_delete,
                switchable: false,
                sortable: false,
                formatter: function(value, row) {
                    let html = '';

                    if (options.allow_edit) {
                        html += makeEditButton('button-edit-stocktake', row.pk, '{% trans "Edit Stocktake Entry" %}');
                    }

                    if (options.allow_delete) {
                        html += makeDeleteButton('button-delete-stocktake', row.pk, '{% trans "Delete Stocktake Entry" %}');
                    }

                    return wrapButtons(html);
                }
            }
        ],
        onPostBody: function() {
            // Button callbacks
            $(table).find('.button-edit-stocktake').click(function() {
                var pk = $(this).attr('pk');

                constructForm(`{% url "api-part-stocktake-list" %}${pk}/`, {
                    fields: {
                        item_count: {},
                        quantity: {},
                        cost_min: {
                            icon: 'fa-dollar-sign',
                        },
                        cost_min_currency: {
                            icon: 'fa-coins',
                        },
                        cost_max: {
                            icon: 'fa-dollar-sign',
                        },
                        cost_max_currency: {
                            icon: 'fa-coins',
                        },
                        note: {
                            icon: 'fa-sticky-note',
                        },
                    },
                    title: '{% trans "Edit Stocktake Entry" %}',
                    refreshTable: table,
                });
            });

            $(table).find('.button-delete-stocktake').click(function() {
                var pk = $(this).attr('pk');

                constructForm(`{% url "api-part-stocktake-list" %}${pk}/`, {
                    method: 'DELETE',
                    title: '{% trans "Delete Stocktake Entry" %}',
                    refreshTable: table,
                });
            });
        }
    });
}


/*
 * Load part variant table
 */
function loadPartVariantTable(table, partId, options={}) {

    var params = options.params || {};

    params.ancestor = partId;

    // Load filters
    var filters = loadTableFilters('variants', params);

    setupFilterList('variants', $(table));

    var cols = [
        {
            field: 'pk',
            title: 'ID',
            visible: false,
            switchable: false,
        },
        {
            field: 'name',
            title: '{% trans "Name" %}',
            switchable: false,
            sortable: true,
            formatter: function(value, row) {
                var html = '';

                var name = row.full_name || row.name;

                if (row.is_template) {
                    name = '<i>' + name + '</i>';
                }

                html += imageHoverIcon(row.thumbnail);
                html += renderLink(name, `/part/${row.pk}/`);

                if (row.trackable) {
                    html += makeIconBadge('fa-directions', '{% trans "Trackable part" %}');
                }

                if (row.virtual) {
                    html += makeIconBadge('fa-ghost', '{% trans "Virtual part" %}');
                }

                if (row.is_template) {
                    html += makeIconBadge('fa-clone', '{% trans "Template part" %}');
                }

                if (row.assembly) {
                    html += makeIconBadge('fa-tools', '{% trans "Assembled part" %}');
                }

                if (!row.active) {
                    html += `<span class='badge badge-right rounded-pill bg-warning'>{% trans "Inactive" %}</span>`;
                }

                return html;
            },
        },
        {
            field: 'IPN',
            title: '{% trans "IPN" %}',
            sortable: true,
        },
        {
            field: 'revision',
            title: '{% trans "Revision" %}',
            switchable: global_settings.PART_ENABLE_REVISION,
            visible: global_settings.PART_ENABLE_REVISION,
            sortable: true,
        },
        {
            field: 'description',
            title: '{% trans "Description" %}',
        },
        {
            field: 'total_in_stock',
            title: '{% trans "Stock" %}',
            sortable: true,
            formatter: function(value, row) {

                var text = renderLink(value, `/part/${row.pk}/?display=part-stock`);

                text += partStockLabel(row, {
                    noDemandInfo: true,
                    hideTotalStock: true,
                    classes: 'float-right',
                });

                if (row.variant_stock > 0) {
                    text = `<em>${text}</em>`;
                    text += `<span title='{% trans "Includes variant stock" %}' class='fas fa-info-circle float-right icon-blue'></span>`;
                }

                return text;
            }
        },
        {
            field: 'price_range',
            title: '{% trans "Price Range" %}',
            formatter: function(value, row) {
                return formatPriceRange(
                    row.pricing_min,
                    row.pricing_max,
                );
            }
        }
    ];

    table.inventreeTable({
        url: '{% url "api-part-list" %}',
        name: 'partvariants',
        showColumns: true,
        original: params,
        queryParams: filters,
        formatNoMatches: function() {
            return '{% trans "No variants found" %}';
        },
        columns: cols,
        treeEnable: true,
        rootParentId: partId,
        parentIdField: 'variant_of',
        idField: 'pk',
        uniqueId: 'pk',
        treeShowField: 'name',
        sortable: true,
        search: true,
        onPostBody: function() {
            table.treegrid({
                treeColumn: 0,
            });

            table.treegrid('collapseAll');
        }
    });
}


/*
 * Load a "simplified" part table without filtering
 */
function loadSimplePartTable(table, url, options={}) {

    options.disableFilters = true;

    loadPartTable(table, url, options);
}


/*
 * Construct a set of fields for the PartParameter model.
 * Note that the 'data' field changes based on the selected parameter template
 */
function partParameterFields(options={}) {

    let fields = {
        part: {
            hidden: true,  // Part is set by the parent form
        },
        template: {
            filters: {
                ordering: 'name',
            },
            onEdit: function(value, name, field, opts) {
                // Callback function when the parameter template is selected.
                // We rebuild the 'data' field based on the template selection

                let checkbox = false;
                let choices = [];

                if (value) {
                    // Request the parameter template data
                    inventreeGet(`{% url "api-part-parameter-template-list" %}${value}/`, {}, {
                        async: false,
                        success: function(response) {
                            if (response.checkbox) {
                                // Checkbox input
                                checkbox = true;
                            } else if (response.choices) {
                                // Select input
                                response.choices.split(',').forEach(function(choice) {
                                    choice = choice.trim();
                                    choices.push({
                                        value: choice,
                                        display_name: choice,
                                    });
                                });
                            }
                        }
                    });
                }

                // Find the current field element
                let el = $(opts.modal).find('#id_data');

                // Extract the current value from the field
                let val = getFormFieldValue('data', {}, opts);

                // Rebuild the field
                let parameters = {};

                if (checkbox) {
                    parameters.type = 'boolean';
                } else if (choices.length > 0) {
                    parameters.type = 'choice';
                    parameters.choices = choices;
                } else {
                    parameters.type = 'string';
                }

                let existing_field_type = guessFieldType(el);

                // If the field type has changed, we need to replace the field
                if (existing_field_type != parameters.type) {
                    // Construct the new field
                    let new_field = constructInput('data', parameters, opts);

                    if (guessFieldType(el) == 'boolean') {
                        // Boolean fields are wrapped in a parent element
                        el.parent().replaceWith(new_field);
                    } else {
                        el.replaceWith(new_field);
                    }
                }

                // Update the field parameters in the form options
                opts.fields.data.type = parameters.type;
                updateFieldValue('data', val, parameters, opts);
            }
        },
        data: {},
    };

    if (options.part) {
        fields.part.value = options.part;
    }

    return fields;
}


/*
 * Launch a modal form for creating a new PartParameter object
 */
function createPartParameter(part_id, options={}) {

    options.fields = partParameterFields({
        part: part_id,
    });

    options.processBeforeUpload = function(data) {
        // Convert data to string
        data.data = data.data.toString();
        return data;
    }

    options.method = 'POST';
    options.title = '{% trans "Add Parameter" %}';

    constructForm('{% url "api-part-parameter-list" %}', options);
}


/*
 * Launch a modal form for editing a PartParameter object
 */
function editPartParameter(param_id, options={}) {
    options.fields = partParameterFields();
    options.title = '{% trans "Edit Parameter" %}';
    options.focus = 'data';

    options.processBeforeUpload = function(data) {
        // Convert data to string
        data.data = data.data.toString();
        return data;
    }

    constructForm(`{% url "api-part-parameter-list" %}${param_id}/`, options);
}


function loadPartParameterTable(table, options) {

    var params = options.params || {};

    // Load filters
    var filters = loadTableFilters('part-parameters', params);

    var filterTarget = options.filterTarget || '#filter-list-parameters';

    setupFilterList('part-parameters', $(table), filterTarget);

    $(table).inventreeTable({
        url: '{% url "api-part-parameter-list" %}',
        original: params,
        queryParams: filters,
        name: 'partparameters',
        groupBy: false,
        formatNoMatches: function() {
            return '{% trans "No parameters found" %}';
        },
        columns: [
            {
                checkbox: true,
                switchable: false,
                visible: true,
            },
            {
                field: 'name',
                title: '{% trans "Name" %}',
                switchable: false,
                sortable: true,
                formatter: function(value, row) {
                    return row.template_detail.name;
                }
            },
            {
                field: 'description',
                title: '{% trans "Description" %}',
                switchable: true,
                sortable: false,
                formatter: function(value, row) {
                    return row.template_detail.description;
                }
            },
            {
                field: 'data',
                title: '{% trans "Value" %}',
                switchable: false,
                sortable: true,
                formatter: function(value, row) {
                    let template = row.template_detail;

                    if (template.checkbox) {
                        return trueFalseLabel(value);
                    }

                    if (row.data_numeric && row.template_detail.units) {
                        return `<span title='${row.data_numeric} ${row.template_detail.units}'>${row.data}</span>`;
                    } else {
                        return row.data;
                    }
                }
            },
            {
                field: 'units',
                title: '{% trans "Units" %}',
                switchable: true,
                sortable: true,
                formatter: function(value, row) {
                    return row.template_detail.units;
                }
            },
            {
                field: 'actions',
                title: '',
                switchable: false,
                sortable: false,
                formatter: function(value, row) {
                    let pk = row.pk;
                    let html = '';

                    html += makeEditButton('button-parameter-edit', pk, '{% trans "Edit parameter" %}');
                    html += makeDeleteButton('button-parameter-delete', pk, '{% trans "Delete parameter" %}');

                    return wrapButtons(html);
                }
            }
        ],
        onPostBody: function() {
            // Setup button callbacks
            $(table).find('.button-parameter-edit').click(function() {
                var pk = $(this).attr('pk');

                editPartParameter(pk, {
                    refreshTable: table
                });
            });

            $(table).find('.button-parameter-delete').click(function() {
                var pk = $(this).attr('pk');

                constructForm(`{% url "api-part-parameter-list" %}${pk}/`, {
                    method: 'DELETE',
                    title: '{% trans "Delete Parameter" %}',
                    refreshTable: table,
                });
            });
        }
    });
}


/*
 * Return a list of fields for a part parameter template
 */
function partParameterTemplateFields() {
    return {
        name: {},
        description: {},
        units: {
            icon: 'fa-ruler',
        },
        choices: {
            icon: 'fa-th-list',
        },
        checkbox: {},
    };
}


/*
 * Construct a table showing a list of part parameter templates
 */
function loadPartParameterTemplateTable(table, options={}) {

    let params = options.params || {};

    params.ordering = 'name';

    let filters = loadTableFilters('part-parameter-templates', params);

    let filterTarget = options.filterTarget || '#filter-list-parameter-templates';

    setupFilterList('part-parameter-templates', $(table), filterTarget);

    $(table).inventreeTable({
        url: '{% url "api-part-parameter-template-list" %}',
        original: params,
        queryParams: filters,
        sortable: true,
        sidePagination: 'server',
        name: 'part-parameter-templates',
        formatNoMatches: function() {
            return '{% trans "No part parameter templates found" %}';
        },
        columns: [
            {
                field: 'pk',
                title: '{% trans "ID" %}',
                visible: false,
                switchable: false,
            },
            {
                field: 'name',
                title: '{% trans "Name" %}',
                sortable: true,
            },
            {
                field: 'units',
                title: '{% trans "Units" %}',
                sortable: true,
                switchable: true,
            },
            {
                field: 'description',
                title: '{% trans "Description" %}',
                sortable: false,
                switchable: true,
            },
            {
                field: 'checkbox',
                title: '{% trans "Checkbox" %}',
                sortable: false,
                switchable: true,
                formatter: function(value) {
                    return yesNoLabel(value);
                }
            },
            {
                field: 'choices',
                title: '{% trans "Choices" %}',
                sortable: false,
                switchable: true,
            },
            {
                formatter: function(value, row, index, field) {

                    let buttons = '';

                    buttons += makeEditButton('template-edit', row.pk, '{% trans "Edit Template" %}');
                    buttons += makeDeleteButton('template-delete', row.pk, '{% trans "Delete Template" %}');

                    return wrapButtons(buttons);
                }
            }
        ]
    });

    $(table).on('click', '.template-edit', function() {
        var button = $(this);
        var pk = button.attr('pk');

        constructForm(
            `/api/part/parameter/template/${pk}/`,
            {
                fields: partParameterTemplateFields(),
                title: '{% trans "Edit Part Parameter Template" %}',
                refreshTable: table,
            }
        );
    });

    $(table).on('click', '.template-delete', function() {
        var button = $(this);
        var pk = button.attr('pk');

        var html = `
        <div class='alert alert-block alert-danger'>
            {% trans "Any parameters which reference this template will also be deleted" %}
        </div>`;

        constructForm(
            `/api/part/parameter/template/${pk}/`,
            {
                method: 'DELETE',
                preFormContent: html,
                title: '{% trans "Delete Part Parameter Template" %}',
                refreshTable: table,
            }
        );
    });
}


/*
 * Construct a table showing a list of purchase orders for a given part.
 *
 * This requests API data from the PurchaseOrderLineItem endpoint
 */
function loadPartPurchaseOrderTable(table, part_id, options={}) {

    options.params = options.params || {};

    // Construct API filterset
    options.params.base_part = part_id;
    options.params.part_detail = true;
    options.params.order_detail = true;

    var filters = loadTableFilters('purchaseorderlineitem', options.params);

    setupFilterList('purchaseorderlineitem', $(table), '#filter-list-partpurchaseorders');

    $(table).inventreeTable({
        url: '{% url "api-po-line-list" %}',
        queryParams: filters,
        name: 'partpurchaseorders',
        original: options.params,
        showColumns: true,
        uniqueId: 'pk',
        formatNoMatches: function() {
            return '{% trans "No purchase orders found" %}';
        },
        onPostBody: function() {
            $(table).find('.button-line-receive').click(function() {
                var pk = $(this).attr('pk');

                var line_item = $(table).bootstrapTable('getRowByUniqueId', pk);

                if (!line_item) {
                    console.warn('getRowByUniqueId returned null');
                    return;
                }

                receivePurchaseOrderItems(
                    line_item.order,
                    [
                        line_item,
                    ],
                    {
                        success: function() {
                            $(table).bootstrapTable('refresh');
                        }
                    }
                );
            });
        },
        columns: [
            {
                field: 'order',
                title: '{% trans "Purchase Order" %}',
                switchable: false,
                formatter: function(value, row) {
                    var order = row.order_detail;

                    if (!order) {
                        return '-';
                    }

                    var html = renderLink(order.reference, `/order/purchase-order/${order.pk}/`);

                    html += purchaseOrderStatusDisplay(
                        order.status,
                        {
                            classes: 'float-right',
                        }
                    );

                    return html;
                },
            },
            {
                field: 'supplier',
                title: '{% trans "Supplier" %}',
                switchable: true,
                formatter: function(value, row) {

                    if (row.supplier_part_detail && row.supplier_part_detail.supplier_detail) {
                        var supp = row.supplier_part_detail.supplier_detail;
                        var html = imageHoverIcon(supp.thumbnail || supp.image);

                        html += ' ' + renderLink(supp.name, `/company/${supp.pk}/`);

                        return html;
                    } else {
                        return '-';
                    }
                }
            },
            {
                field: 'sku',
                title: '{% trans "SKU" %}',
                switchable: true,
                formatter: function(value, row) {
                    if (row.supplier_part_detail) {
                        var supp = row.supplier_part_detail;

                        return renderClipboard(renderLink(supp.SKU, `/supplier-part/${supp.pk}/`));
                    } else {
                        return '-';
                    }
                },
            },
            {
                field: 'mpn',
                title: '{% trans "MPN" %}',
                switchable: true,
                formatter: function(value, row) {
                    if (row.supplier_part_detail && row.supplier_part_detail.manufacturer_part_detail) {
                        var manu = row.supplier_part_detail.manufacturer_part_detail;
                        return renderClipboard(renderLink(manu.MPN, `/manufacturer-part/${manu.pk}/`));
                    }
                }
            },
            {
                field: 'quantity',
                title: '{% trans "Quantity" %}',
                formatter: function(value, row) {
                    let data = value;

                    if (row.supplier_part_detail && row.supplier_part_detail.pack_quantity_native != 1.0) {
                        let pq = row.supplier_part_detail.pack_quantity_native;
                        let total = value * pq;

                        data += makeIconBadge(
                            'fa-info-circle icon-blue',
                            `{% trans "Pack Quantity" %}: ${pq} - {% trans "Total Quantity" %}: ${total}`
                        );
                    }

                    return data;
                },
            },
            {
                field: 'target_date',
                title: '{% trans "Target Date" %}',
                switchable: true,
                sortable: true,
                formatter: function(value, row) {

                    var target = row.target_date || row.order_detail.target_date;

                    var today = moment();

                    var overdue = row.overdue || false;

                    if (target) {
                        if (moment(target) < today) {
                            overdue = true;
                        }
                    }

                    var html = '-';

                    if (row.target_date) {
                        html = row.target_date;


                    } else if (row.order_detail && row.order_detail.target_date) {
                        html = `<em>${row.order_detail.target_date}</em>`;
                    }

                    if (overdue) {
                        html += makeIconBadge(
                            'fa-calendar-alt icon-red',
                            '{% trans "This line item is overdue" %}',
                        );
                    }

                    return html;
                }
            },
            {
                field: 'received',
                title: '{% trans "Received" %}',
                switchable: true,
                formatter: function(value, row) {
                    var data = value;

                    if (value > 0 && row.supplier_part_detail && row.supplier_part_detail.pack_quantity_native != 1.0) {
                        let pq = row.supplier_part_detail.pack_quantity_native;
                        let total = value * pq;
                        data += `<span class='fas fa-info-circle icon-blue float-right' title='{% trans "Pack Quantity" %}: ${pq} - {% trans "Total Quantity" %}: ${total}'></span>`;
                    }

                    return data;
                },
            },
            {
                field: 'purchase_price',
                title: '{% trans "Price" %}',
                switchable: true,
                formatter: function(value, row) {
                    return formatCurrency(row.purchase_price, {
                        currency: row.purchase_price_currency,
                    });
                }
            },
            {
                field: 'actions',
                title: '',
                switchable: false,
                formatter: function(value, row) {

                    if (row.received >= row.quantity) {
                        // Already received
                        return `<span class='badge bg-success rounded-pill'>{% trans "Received" %}</span>`;
                    } else if (row.order_detail && row.order_detail.status == {{ PurchaseOrderStatus.PLACED }}) {
                        let html = '';
                        var pk = row.pk;

                        html += makeIconButton('fa-sign-in-alt', 'button-line-receive', pk, '{% trans "Receive line item" %}');

                        return wrapButtons(html);
                    } else {
                        return '';
                    }
                }
            }
        ],
    });
}


function loadRelatedPartsTable(table, part_id, options={}) {
    /*
     * Load table of "related" parts
     */

    options.params = options.params || {};

    options.params.part = part_id;

    var filters = Object.assign({}, options.params);

    setupFilterList('related', $(table), options.filterTarget);

    function getPart(row) {
        if (row.part_1 == part_id) {
            return row.part_2_detail;
        } else {
            return row.part_1_detail;
        }
    }

    var columns = [
        {
            field: 'name',
            title: '{% trans "Part" %}',
            switchable: false,
            formatter: function(value, row) {

                var part = getPart(row);

                var html = imageHoverIcon(part.thumbnail) + renderLink(part.full_name, `/part/${part.pk}/`);

                html += makePartIcons(part);

                return html;
            }
        },
        {
            field: 'description',
            title: '{% trans "Description" %}',
            formatter: function(value, row) {
                return getPart(row).description;
            }
        },
        {
            field: 'actions',
            title: '',
            switchable: false,
            formatter: function(value, row) {
                let html = '';
                html += makeDeleteButton('button-related-delete', row.pk, '{% trans "Delete part relationship" %}');

                return wrapButtons(html);
            }
        }
    ];

    $(table).inventreeTable({
        url: '{% url "api-part-related-list" %}',
        groupBy: false,
        name: 'related',
        original: options.params,
        queryParams: filters,
        columns: columns,
        showColumns: false,
        search: true,
        onPostBody: function() {
            $(table).find('.button-related-delete').click(function() {
                var pk = $(this).attr('pk');

                constructForm(`{% url "api-part-related-list" %}${pk}/`, {
                    method: 'DELETE',
                    title: '{% trans "Delete Part Relationship" %}',
                    refreshTable: table,
                });
            });
        },
    });
}


/* Load parametric table for part parameters
 */
function loadParametricPartTable(table, options={}) {

    options.params = options.params || {};

    options.params['parameters'] = true;

    let filters = loadTableFilters('parameters', options.params);

    setupFilterList('parameters', $(table), '#filter-list-parameters');

    var columns = [
        {
            field: 'name',
            title: '{% trans "Part" %}',
            switchable: false,
            sortable: true,
            formatter: function(value, row) {
                var name = row.full_name;

                var display = imageHoverIcon(row.thumbnail) + renderLink(name, `/part/${row.pk}/`);

                return display;
            }
        }
    ];

    // Request a list of parameters we are interested in for this category
    inventreeGet(
        '{% url "api-part-parameter-template-list" %}',
        {
            category: options.category,
        },
        {
            async: false,
            success: function(response) {
                for (var template of response) {

                    let template_name = template.name;

                    if (template.units) {
                        template_name += ` [${template.units}]`;
                    }

                    let fmt_func = null;

                    if (template.checkbox) {
                        fmt_func = function(value) {
                            if (value == null) {
                                return null;
                            } else {
                                return trueFalseLabel(value);
                            }
                        }
                    }

                    columns.push({
                        field: `parameter_${template.pk}`,
                        title: template_name,
                        switchable: true,
                        sortable: true,
                        filterControl: 'input',
                        visible: false,
                        formatter: fmt_func,
                    });
                }
            }
        }
    );


    $(table).inventreeTable({
        url: '{% url "api-part-list" %}',
        queryParams: filters,
        original: options.params,
        groupBy: false,
        name: options.name || 'part-parameters',
        formatNoMatches: function() {
            return '{% trans "No parts found" %}';
        },
        // TODO: Re-enable filter control for parameter values
        // Ref: https://github.com/inventree/InvenTree/issues/4851
        // filterControl: true,
        // showFilterControlSwitch: true,
        // sortSelectOptions: true,
        columns: columns,
        showColumns: true,
        sidePagination: 'server',
        idField: 'pk',
        uniqueId: 'pk',
        onLoadSuccess: function(response) {

            // Display columns as we receive data from them
            let activated_columns = [];

            // Data may be returned paginated, in which case we preference response.results
            var data = response.results || response;

            for (var idx = 0; idx < data.length; idx++) {
                var row = data[idx];

                // Make each parameter accessible, based on the "template" columns
                row.parameters.forEach(function(parameter) {
                    let col_name = `parameter_${parameter.template}`;
                    row[col_name] = parameter.data;

                    // Display the column if it is not already displayed
                    if (!activated_columns.includes(col_name)) {
                        activated_columns.push(col_name);
                        $(table).bootstrapTable('showColumn', col_name);
                    }
                });

                data[idx] = row;
            }

            if (response.results) {
                response.results = data;
            } else {
                response = data;
            }

            // Update the table
            $(table).bootstrapTable('load', response);
        }
    });
}


// Generate a "grid tile" view for a particular part
function partGridTile(part) {

    // Rows for table view
    var rows = '';

    var units = part.units || '';
    var stock = `${part.in_stock} ${units}`;

    if (!part.in_stock) {
        stock = `<span class='badge rounded-pill bg-danger'>{% trans "No Stock" %}</span>`;
    } else if (!part.unallocated_stock) {
        stock = `<span class='badge rounded-pill bg-warning'>{% trans "No Stock" %}</span>`;
    }

    rows += `<tr><td><b>{% trans "Stock" %}</b></td><td>${stock}</td></tr>`;

    if (part.ordering) {
        rows += `<tr><td><b>{% trans "On Order" %}</b></td><td>${part.ordering} ${units}</td></tr>`;
    }

    if (part.building) {
        rows += `<tr><td><b>{% trans "Building" %}</b></td><td>${part.building} ${units}</td></tr>`;
    }

    var html = `

    <div class='card product-card borderless'>
        <div class='panel product-card-panel'>
            <div class='panel-heading'>
                <a href='/part/${part.pk}/'>
                    <b>${part.full_name}</b>
                </a>
                ${makePartIcons(part)}
                <br>
                <i>${part.description}</i>
            </div>
            <div class='panel-content'>
                <div class='row'>
                    <div class='col-sm-4'>
                        <img src='${part.thumbnail}' class='card-thumb' onclick='showModalImage("${part.image}")'>
                    </div>
                    <div class='col-sm-8'>
                        <table class='table table-striped table-condensed'>
                            ${rows}
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `;

    return html;
}


/*
 * Update the category for a set of parts
 */
function setPartCategory(data, options={}) {

    let parts = [];

    data.forEach(function(item) {
        parts.push(item.pk);
    });

    var html = `
    <div class='alert alert-block alert-info'>
        {% trans "Set the part category for the selected parts" %}
    </div>
    `;

    constructForm('{% url "api-part-change-category" %}',{
        title: '{% trans "Set Part Category" %}',
        method: 'POST',
        preFormContent: html,
        fields: {
            category: {
                tree_picker: {
                    url: '{% url "api-part-category-tree" %}',
                    default_icon: global_settings.PART_CATEGORY_DEFAULT_ICON,
                },
            },
        },
        processBeforeUpload: function(data) {
            data.parts = parts;
            return data;
        },
        onSuccess: function() {
            $(options.table).bootstrapTable('refresh');
        }
    });
}


/*
 * Construct a set of custom actions for the part table
 */
function makePartActions(table) {

    return [
        {
            label: 'set-category',
            title: '{% trans "Set category" %}',
            icon: 'fa-sitemap',
            permission: 'part.change',
            callback: function(data) {
                setPartCategory(data, {table: table});
            }
        },
        {
            label: 'order',
            title: '{% trans "Order parts" %}',
            icon: 'fa-shopping-cart',
            permission: 'purchase_order.add',
            callback: function(data) {
                orderParts(data);
            },
        }
    ]
}


/* Load part listing data into specified table.
 *
 * Args:
 *  - table: HTML reference to the table
 *  - url: Base URL for API query
 *  - options: object containing following (optional) fields
 *      checkbox: Show the checkbox column
 *      query: extra query params for API request
 *      buttons: If provided, link buttons to selection status of this table
 *      disableFilters: If true, disable custom filters
 *      actions: Provide a callback function to construct an "actions" column
 */
function loadPartTable(table, url, options={}) {

    options.params = options.params || {};

    let table_name = options.name || 'parts';

    // Ensure category detail is included
    options.params['category_detail'] = true;

    let filters = {};

    if (!options.disableFilters) {
        filters = loadTableFilters(table_name, options.params);

        setupFilterList('parts', $(table), options.filterTarget, {
            download: true,
            labels: {
                url: '{% url "api-part-label-list" %}',
                key: 'part',
            },
            singular_name: '{% trans "part" %}',
            plural_name: '{% trans "parts" %}',
            custom_actions: [
                {
                    label: 'parts',
                    icon: 'fa-tools',
                    title: '{% trans "Part actions" %}',
                    actions: makePartActions(table),
                }
            ]
        });
    }

    // Update fields with passed parameters
    filters = Object.assign(filters, options.params);

    var columns = [
        {
            field: 'pk',
            title: 'ID',
            visible: false,
            switchable: false,
            searchable: false,
        }
    ];

    if (options.checkbox) {
        columns.push({
            checkbox: true,
            title: '{% trans "Select" %}',
            searchable: false,
            switchable: false,
        });
    }

    columns.push({
        field: 'name',
        title: '{% trans "Part" %}',
        switchable: false,
        sortable: !options.params.ordering,
        formatter: function(value, row) {

            var name = shortenString(row.full_name);

            var display = imageHoverIcon(row.thumbnail) + renderLink(name, `/part/${row.pk}/`);

            display += makePartIcons(row);

            return withTitle(display, row.full_name);
        }
    });

    columns.push({
        field: 'IPN',
        title: '{% trans "IPN" %}',
        sortable: !options.params.ordering
    });

    columns.push({
        field: 'revision',
        title: '{% trans "Revision" %}',
        switchable: global_settings.PART_ENABLE_REVISION,
        visible: global_settings.PART_ENABLE_REVISION,
        sortable: true,
    });

    columns.push({
        field: 'description',
        title: '{% trans "Description" %}',
        formatter: function(value, row) {

            var text = shortenString(value);

            if (row.is_template) {
                text = `<i>${text}</i>`;
            }

            return withTitle(text, row.description);
        }
    });

    columns.push({
        field: 'units',
        title: '{% trans "Units" %}',
        sortable: true,
    });

    columns.push({
        sortName: 'category',
        field: 'category_detail',
        title: '{% trans "Category" %}',
        sortable: true,
        formatter: function(value, row) {
            if (row.category && row.category_detail) {
                var text = shortenString(row.category_detail.pathstring);
                return withTitle(renderLink(text, `/part/category/${row.category}/`), row.category_detail.pathstring);
            } else {
                return '<em>{% trans "No category" %}</em>';
            }
        }
    });


    columns.push({
        field: 'total_in_stock',
        title: '{% trans "Stock" %}',
        sortable: true,
        formatter: function(value, row) {

            var text = renderLink(value, `/part/${row.pk}/?display=part-stock`);

            text += partStockLabel(row, {
                noDemandInfo: true,
                hideTotalStock: true,
                classes: 'float-right',
            });

            return text;
        },
        footerFormatter: function(data) {
            // Display "total" stock quantity of all rendered rows
            // Requires that all parts have the same base units!

            let total = 0;
            let units = new Set();

            data.forEach(function(row) {
                units.add(row.units || null);
                if (row.total_in_stock != null) {
                    total += row.total_in_stock;
                }
            });

            if (data.length == 0) {
                return '-';
            } else if (units.size > 1) {
                return '-';
            } else {
                let output = `${total}`;

                if (units.size == 1) {
                    let unit = units.values().next().value;

                    if (unit) {
                        output += ` [${unit}]`;
                    }
                }

                return output;
            }
        }
    });

    // Pricing information
    columns.push({
        field: 'pricing_min',
        sortable: false,
        title: '{% trans "Price Range" %}',
        formatter: function(value, row) {
            return formatPriceRange(
                row.pricing_min,
                row.pricing_max
            );
        }
    });

    // External link / URL
    columns.push({
        field: 'link',
        title: '{% trans "Link" %}',
        formatter: function(value) {
            return renderLink(
                value,
                value,
                {
                    remove_http: true,
                    tooltip: true,
                }
            );
        }
    });

    columns.push({
        field: 'last_stocktake',
        title: '{% trans "Last Stocktake" %}',
        sortable: true,
        switchable: true,
        formatter: function(value) {
            return renderDate(value);
        }
    });

    // Push an "actions" column
    if (options.actions) {
        columns.push({
            field: 'actions',
            title: '',
            switchable: false,
            visible: true,
            searchable: false,
            sortable: false,
            formatter: function(value, row) {
                return options.actions(value, row);
            }
        });
    }

    var grid_view = options.gridView && inventreeLoad('part-grid-view') == 1;

    $(table).inventreeTable({
        url: url,
        method: 'get',
        name: table_name,
        queryParams: filters,
        groupBy: false,
        original: options.params,
        sidePagination: 'server',
        pagination: 'true',
        formatNoMatches: function() {
            return '{% trans "No parts found" %}';
        },
        columns: columns,
        showColumns: true,
        showCustomView: grid_view,
        showCustomViewButton: false,
        showFooter: true,
        onPostBody: function() {
            grid_view = inventreeLoad('part-grid-view') == 1;
            if (grid_view) {
                $('#view-part-list').removeClass('btn-secondary').addClass('btn-outline-secondary');
                $('#view-part-grid').removeClass('btn-outline-secondary').addClass('btn-secondary');
            } else {
                $('#view-part-grid').removeClass('btn-secondary').addClass('btn-outline-secondary');
                $('#view-part-list').removeClass('btn-outline-secondary').addClass('btn-secondary');
            }

            if (options.onPostBody) {
                options.onPostBody();
            }
        },
        buttons: options.gridView ? [
            {
                icon: 'fas fa-bars',
                attributes: {
                    title: '{% trans "Display as list" %}',
                    id: 'view-part-list',
                },
                event: () => {
                    inventreeSave('part-grid-view', 0);
                    $(table).bootstrapTable(
                        'refreshOptions',
                        {
                            showCustomView: false,
                        }
                    );
                }
            },
            {
                icon: 'fas fa-th',
                attributes: {
                    title: '{% trans "Display as grid" %}',
                    id: 'view-part-grid',
                },
                event: () => {
                    inventreeSave('part-grid-view', 1);
                    $(table).bootstrapTable(
                        'refreshOptions',
                        {
                            showCustomView: true,
                        }
                    );
                }
            }
        ] : [],
        customView: function(data) {

            var html = '';

            html = `<div class='row full-height'>`;

            data.forEach(function(row, index) {

                // Force a new row every 5 columns
                if ((index > 0) && (index % 5 == 0) && (index < data.length)) {
                    html += `</div><div class='row full-height'>`;
                }

                html += partGridTile(row);
            });

            html += `</div>`;

            return html;
        }
    });
}


/*
 * Display a table of part categories
 */
function loadPartCategoryTable(table, options) {

    var params = options.params || {};

    var filterListElement = options.filterList || '#filter-list-category';

    var filterKey = options.filterKey || options.name || 'category';

    var tree_view = options.allowTreeView && inventreeLoad('category-tree-view') == 1;

    if (tree_view) {
        params.cascade = true;
        params.depth = global_settings.INVENTREE_TREE_DEPTH;
    }

    let filters = loadTableFilters(filterKey, params);

    setupFilterList(filterKey, table, filterListElement, {download: true});

    // Function to request sub-category items
    function requestSubItems(parent_pk) {
        inventreeGet(
            options.url || '{% url "api-part-category-list" %}',
            {
                parent: parent_pk,
            },
            {
                success: function(response) {
                    // Add the returned sub-items to the table
                    for (var idx = 0; idx < response.length; idx++) {
                        response[idx].parent = parent_pk;
                    }

                    const row = $(table).bootstrapTable('getRowByUniqueId', parent_pk);
                    row.subReceived = true;

                    $(table).bootstrapTable('updateByUniqueId', parent_pk, row, true);

                    table.bootstrapTable('append', response);
                },
                error: function(xhr) {
                    console.error('Error requesting sub-category for category=' + parent_pk);
                    showApiError(xhr);
                }
            }
        );
    }

    table.inventreeTable({
        treeEnable: tree_view,
        rootParentId: tree_view ? options.params.parent : null,
        uniqueId: 'pk',
        idField: 'pk',
        treeShowField: 'name',
        parentIdField: tree_view ? 'parent' : null,
        method: 'get',
        formatNoMatches: function() {
            return '{% trans "No subcategories found" %}';
        },
        url: options.url || '{% url "api-part-category-list" %}',
        queryParams: filters,
        disablePagination: tree_view,
        sidePagination: tree_view ? 'client' : 'server',
        serverSort: !tree_view,
        search: !tree_view,
        name: 'category',
        original: params,
        showColumns: true,
        sortable: true,
        buttons: options.allowTreeView ? [
            {
                icon: 'fas fa-bars',
                attributes: {
                    title: '{% trans "Display as list" %}',
                    id: 'view-category-list',
                },
                event: () => {
                    inventreeSave('category-tree-view', 0);

                    // Adjust table options
                    options.treeEnable = false;
                    options.serverSort = false;
                    options.search = true;
                    options.pagination = true;

                    // Destroy and re-create the table
                    table.bootstrapTable('destroy');
                    loadPartCategoryTable(table, options);
                }
            },
            {
                icon: 'fas fa-sitemap',
                attributes: {
                    title: '{% trans "Display as tree" %}',
                    id: 'view-category-tree',
                },
                event: () => {
                    inventreeSave('category-tree-view', 1);

                    // Adjust table options
                    options.treeEnable = true;
                    options.serverSort = false;
                    options.search = false;
                    options.pagination = false;

                    // Destroy and re-create the table
                    table.bootstrapTable('destroy');
                    loadPartCategoryTable(table, options);
                }
            }
        ] : [],
        onPostBody: function() {

            if (options.allowTreeView) {

                tree_view = inventreeLoad('category-tree-view') == 1;

                if (tree_view) {

                    $('#view-category-list').removeClass('btn-secondary').addClass('btn-outline-secondary');
                    $('#view-category-tree').removeClass('btn-outline-secondary').addClass('btn-secondary');

                    table.treegrid({
                        treeColumn: 0,
                        onChange: function() {
                            table.bootstrapTable('resetView');
                        },
                        onExpand: function() {

                        }
                    });

                    // Callback for 'load sub category' button
                    $(table).find('.load-sub-category').click(function(event) {
                        event.preventDefault();

                        const pk = $(this).attr('pk');
                        const row = $(table).bootstrapTable('getRowByUniqueId', pk);

                        // Request sub-category for this category
                        requestSubItems(row.pk);

                        row.subRequested = true;
                        $(table).bootstrapTable('updateByUniqueId', pk, row, true);
                    });
                } else {
                    $('#view-category-tree').removeClass('btn-secondary').addClass('btn-outline-secondary');
                    $('#view-category-list').removeClass('btn-outline-secondary').addClass('btn-secondary');
                }
            }
        },
        columns: [
            {
                checkbox: true,
                title: '{% trans "Select" %}',
                searchable: false,
                switchable: false,
                visible: false,
            },
            {
                field: 'name',
                title: '{% trans "Name" %}',
                switchable: true,
                sortable: true,
                formatter: function(value, row) {
                    let html = '';

                    if (row._level >= global_settings.INVENTREE_TREE_DEPTH && !row.subReceived) {
                        if (row.subRequested) {
                            html += `<a href='#'><span class='fas fa-sync fa-spin'></span></a>`;
                        } else {
                            html += `
                                <a href='#' pk='${row.pk}' class='load-sub-category'>
                                    <span class='fas fa-sync-alt' title='{% trans "Load Subcategories" %}'></span>
                                </a> `;
                        }
                    }

                    const icon = row.icon || global_settings.PART_CATEGORY_DEFAULT_ICON;
                    if (icon) {
                        html += `<span class="${icon} me-1"></span>`;
                    }

                    html += renderLink(
                        value,
                        `/part/category/${row.pk}/`,
                    );

                    if (row.starred) {
                        html += makeIconBadge('fa-bell icon-green', '{% trans "Subscribed category" %}');
                    }

                    return html;
                }
            },
            {
                field: 'description',
                title: '{% trans "Description" %}',
                switchable: true,
                sortable: false,
                formatter: function(value) {
                    return withTitle(shortenString(value), value);
                }
            },
            {
                field: 'pathstring',
                title: '{% trans "Path" %}',
                switchable: !tree_view,
                visible: !tree_view,
                sortable: true,
                formatter: function(value) {
                    return withTitle(shortenString(value), value);
                }
            },
            {
                field: 'part_count',
                title: '{% trans "Parts" %}',
                switchable: true,
                sortable: true,
            }
        ]
    });
}


/* Construct a set of fields for the PartTestTemplate model form */
function partTestTemplateFields(options={}) {
    let fields = {
        test_name: {},
        description: {},
        required: {},
        requires_value: {},
        requires_attachment: {},
        enabled: {},
        part: {
            hidden: true,
        }
    };

    if (options.part) {
        fields.part.value = options.part;
    }

    return fields;
}


/*
 * Load PartTestTemplate table.
 */
function loadPartTestTemplateTable(table, options) {

    var params = options.params || {};

    var part = options.part || null;

    var filterListElement = options.filterList || '#filter-list-parttests';

    var filters = loadTableFilters('parttests', params);

    setupFilterList('parttests', table, filterListElement);

    filters = Object.assign(filters, params);

    table.inventreeTable({
        method: 'get',
        formatNoMatches: function() {
            return '{% trans "No test templates matching query" %}';
        },
        url: '{% url "api-part-test-template-list" %}',
        queryParams: filters,
        name: 'testtemplate',
        original: params,
        columns: [
            {
                field: 'pk',
                title: 'ID',
                visible: false,
                switchable: false,
            },
            {
                field: 'test_name',
                title: '{% trans "Test Name" %}',
                sortable: true,
                formatter: function(value, row) {
                    let html = value;

                    if (row.results && row.results > 0) {
                        html += `
                        <span class='badge bg-dark rounded-pill float-right' title='${row.results} {% trans "results" %}'>
                            ${row.results}
                        </span>`;
                    }

                    return html;
                }
            },
            {
                field: 'description',
                title: '{% trans "Description" %}',
            },
            {
                field: 'enabled',
                title: '{% trans "Enabled" %}',
                sortable: true,
                formatter: function(value) {
                    return yesNoLabel(value);
                }
            },
            {
                field: 'required',
                title: '{% trans "Required" %}',
                sortable: true,
                formatter: function(value) {
                    return yesNoLabel(value);
                }
            },
            {
                field: 'requires_value',
                title: '{% trans "Requires Value" %}',
                formatter: function(value) {
                    return yesNoLabel(value);
                }
            },
            {
                field: 'requires_attachment',
                title: '{% trans "Requires Attachment" %}',
                formatter: function(value) {
                    return yesNoLabel(value);
                }
            },
            {
                field: 'buttons',
                formatter: function(value, row) {
                    var pk = row.pk;

                    if (row.part == part) {
                        let html = '';

                        html += makeEditButton('button-test-edit', pk, '{% trans "Edit test result" %}');
                        html += makeDeleteButton('button-test-delete', pk, '{% trans "Delete test result" %}');

                        return wrapButtons(html);
                    } else {
                        var text = '{% trans "This test is defined for a parent part" %}';

                        return renderLink(text, `/part/${row.part}/?display=test-templates`);
                    }
                }
            }
        ],
        onPostBody: function() {

            table.find('.button-test-edit').click(function() {
                var pk = $(this).attr('pk');

                var url = `/api/part/test-template/${pk}/`;

                constructForm(url, {
                    fields: partTestTemplateFields(),
                    title: '{% trans "Edit Test Result Template" %}',
                    onSuccess: function() {
                        table.bootstrapTable('refresh');
                    },
                });
            });

            table.find('.button-test-delete').click(function() {
                var pk = $(this).attr('pk');

                var url = `/api/part/test-template/${pk}/`;

                constructForm(url, {
                    method: 'DELETE',
                    title: '{% trans "Delete Test Result Template" %}',
                    refreshTable: table,
                });
            });
        }
    });
}


/*
 * Load a chart which displays projected scheduling information for a particular part.
 * This takes into account:
 * - Current stock levels / availability
 * - Upcoming / scheduled build orders
 * - Upcoming / scheduled sales orders
 * - Upcoming / scheduled purchase orders
 */
function loadPartSchedulingChart(canvas_id, part_id) {

    var part_info = null;

    var was_error = false;

    // First, grab updated data for the particular part
    inventreeGet(`{% url "api-part-list" %}${part_id}/`, {}, {
        async: false,
        success: function(response) {
            part_info = response;
        }
    });

    if (!part_info) {
        console.error(`Error loading part information for part ${part_id}`);
        return;
    }

    var today = moment();

    /* Construct initial datasets for:
     * - Scheduled quantity
     * - Minimum speculative quantity
     * - Maximum speculative quantity
     */

    var quantity_scheduled = [{
        date: today,
        delta: 0,
    }];

    // We will construct the HTML table as we go
    var table_html = '';

    // The "known" initial stock quantity
    var initial_stock_min = part_info.in_stock;
    var initial_stock_max = part_info.in_stock;

    var n_entries = 0;

    /* Request scheduling information for the part.
     * Note that this information has already been 'curated' by the server,
     * and arranged in increasing chronological order
     */
    inventreeGet(
        `{% url "api-part-list" %}${part_id}/scheduling/`,
        {},
        {
            async: false,
            success: function(response) {

                n_entries = response.length;

                for (var idx = 0; idx < response.length; idx++) {

                    var entry = response[idx];
                    var date = entry.date != null ? moment(entry.date) : null;

                    var date_string = entry.date;

                    if (date == null) {
                        date_string = '<em>{% trans "No date specified" %}</em>';
                        date_string += makeIconBadge('fa-exclamation-circle icon-red', '{% trans "No date specified" %}');
                    } else if (date < today) {
                        date_string += makeIconBadge('fa-exclamation-circle icon-yellow', '{% trans "Specified date is in the past" %}');
                    }

                    var quantity_string = entry.quantity + entry.speculative_quantity;

                    if (entry.speculative_quantity != 0) {
                        quantity_string += makeIconBadge('fa-question-circle icon-blue', '{% trans "Speculative" %}');
                    }

                    // Add an entry to the scheduling table
                    table_html += `
                        <tr>
                            <td><a href="${entry.url}">${entry.label}</a></td>
                            <td>${entry.title}</td>
                            <td>${date_string}</td>
                            <td>${quantity_string}</td>
                        </tr>
                    `;

                    // If the date is unknown or in the past, we cannot make use of this information
                    // So we update the "speculative quantity"
                    if (date == null || date < today) {
                        if (entry.quantity < 0) initial_stock_min += entry.quantity;
                        if (entry.speculative_quantity < 0) initial_stock_min += entry.speculative_quantity;

                        if (entry.quantity > 0) initial_stock_max += entry.quantity;
                        if (entry.speculative_quantity > 0) initial_stock_max += entry.speculative_quantity;

                        // We do not add this entry to the graph
                        continue;
                    }

                    // Add an entry to the scheduled quantity
                    quantity_scheduled.push({
                        date: moment(entry.date),
                        delta: entry.quantity,
                        speculative: entry.speculative_quantity,
                        title: entry.title,
                        label: entry.label,
                        url: entry.url,
                    });
                }
            },
            error: function(response) {
                console.error(`Error retrieving scheduling information for part ${part_id}`);
                was_error = true;
            }
        }
    );

    // If no scheduling information is available for the part,
    // remove the chart and display a message instead
    if (n_entries < 1) {

        var message = `
        <div class='alert alert-block alert-info'>
            {% trans "No scheduling information available for this part" %}.
        </div>`;

        if (was_error) {
            message = `
                <div class='alert alert-block alert-danger'>
                    {% trans "Error fetching scheduling information for this part" %}.
                </div>
            `;
        }

        var canvas_element = $('#part-schedule-chart');

        canvas_element.closest('div').html(message);

        $('#part-schedule-table').hide();

        return;
    }

    $('#part-schedule-table').show();

    var y_min = 0;
    var y_max = 0;

    // Iterate through future "events" to calculate expected quantity values
    var quantity = part_info.in_stock;
    var speculative_min = initial_stock_min;
    var speculative_max = initial_stock_max;

    // Datasets for speculative quantity
    var q_spec_min = [];
    var q_spec_max = [];

    for (var idx = 0; idx < quantity_scheduled.length; idx++) {

        var speculative = quantity_scheduled[idx].speculative;
        var date = quantity_scheduled[idx].date.format('YYYY-MM-DD');
        var delta = quantity_scheduled[idx].delta;

        // Update the running quantity
        quantity += delta;

        quantity_scheduled[idx].x = date;
        quantity_scheduled[idx].y = quantity;

        // Update minimum "speculative" quantity
        speculative_min += delta;
        speculative_max += delta;

        if (speculative < 0) {
            speculative_min += speculative;
        } else if (speculative > 0) {
            speculative_max += speculative;
        }

        q_spec_min.push({
            x: date,
            y: speculative_min,
            label: '',
            title: '',
        });

        q_spec_max.push({
            x: date,
            y: speculative_max,
            label: '',
            title: '',
        });

        // Update min / max values
        if (quantity < y_min) y_min = quantity;
        if (quantity > y_max) y_max = quantity;

        if (speculative_min < y_min) y_min = speculative_min;
        if (speculative_max > y_max) y_max = speculative_max;
    }

    // Add one extra data point at the end
    var n = quantity_scheduled.length;
    var final_date = quantity_scheduled[n - 1].date.add(1, 'd').format('YYYY-MM-DD');

    quantity_scheduled.push({
        x: final_date,
        y: quantity_scheduled[n - 1].y,
    });

    q_spec_min.push({
        x: final_date,
        y: q_spec_min[n - 1].y,
    });

    q_spec_max.push({
        x: final_date,
        y: q_spec_max[n - 1].y,
    });

    var context = document.getElementById(canvas_id);

    var data = {
        datasets: [
            {
                label: '{% trans "Scheduled Stock Quantities" %}',
                data: quantity_scheduled,
                backgroundColor: 'rgba(160, 80, 220, 0.75)',
                borderWidth: 3,
                borderColor: 'rgb(160, 80, 220)'
            },
            {
                label: '{% trans "Minimum Quantity" %}',
                data: q_spec_min,
                backgroundColor: 'rgba(220, 160, 80, 0.25)',
                borderWidth: 2,
                borderColor: 'rgba(220, 160, 80, 0.35)',
                borderDash: [10, 5],
                fill: '-1',
            },
            {
                label: '{% trans "Maximum Quantity" %}',
                data: q_spec_max,
                backgroundColor: 'rgba(220, 160, 80, 0.25)',
                borderWidth: 2,
                borderColor: 'rgba(220, 160, 80, 0.35)',
                borderDash: [10, 5],
                fill: '-2',
            },
        ],
    };

    var t_min = quantity_scheduled[0].x;
    var t_max = quantity_scheduled[quantity_scheduled.length - 1].x;

    // Construct a 'zero stock' threshold line
    data.datasets.push({
        data: [
            {
                x: t_min,
                y: 0,
            },
            {
                x: t_max,
                y: 0,
            }
        ],
        borderColor: 'rgba(250, 50, 50, 0.75)',
        label: 'zero-stock-level',
    });

    // Construct a 'minimum stock' threshold line
    if (part_info.minimum_stock) {
        var minimum_stock_curve = [
            {
                x: t_min,
                y: part_info.minimum_stock,
            },
            {
                x: t_max,
                y: part_info.minimum_stock,
            }
        ];

        data.datasets.push({
            data: minimum_stock_curve,
            label: '{% trans "Minimum Stock Level" %}',
            backgroundColor: 'rgba(250, 50, 50, 0.1)',
            borderColor: 'rgba(250, 50, 50, 0.5)',
            borderDash: [5, 5],
            fill: {
                target: {
                    value: 0,
                }
            }
        });
    }

    // Update the table
    $('#part-schedule-table').find('tbody').html(table_html);

    if (y_max < part_info.minimum_stock) {
        y_max = part_info.minimum_stock;
    }

    var y_range = y_max - y_min;

    y_max += 0.1 * y_range;
    y_min -= 0.1 * y_range;

    // Prevent errors if y-scale is weird
    if (y_max == y_min) {
        y_min -= 1;
        y_max += 1;
    }

    return new Chart(context, {
        type: 'scatter',
        data: data,
        options: {
            showLine: true,
            stepped: true,
            scales: {
                x: {
                    type: 'time',
                    suggestedMin: today.format(),
                    suggestedMax: quantity_scheduled[quantity_scheduled.length - 1].x,
                    position: 'bottom',
                    time: {
                        minUnit: 'day',
                    },
                },
                y: {
                    suggestedMin: y_min,
                    suggestedMax: y_max,
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(item) {
                            return item.raw.label || '';
                        },
                        beforeLabel: function(item) {
                            return item.raw.title || '';
                        },
                        afterLabel: function(item) {
                            var delta = item.raw.delta;

                            if (delta == null || delta == 0) {
                                delta = '';
                            } else {
                                delta = ` (${item.raw.delta > 0 ? '+' : ''}${item.raw.delta})`;
                            }

                            return `{% trans "Quantity" %}: ${item.raw.y}${delta}`;
                        }
                    }
                },
                legend: {
                    labels: {
                        filter: function(item, chart) {
                            return !item.text.includes('zero-stock-level');
                        }
                    }
                },
            },
        }
    });
}
