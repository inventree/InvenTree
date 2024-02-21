{% load i18n %}
{% load generic %}
{% load inventree_extras %}

/* globals
    buildCodes,
    global_settings,
    inventreeGet,
    purchaseOrderCodes,
    returnOrderCodes,
    returnOrderLineItemCodes,
    salesOrderCodes,
    stockCodes,
*/

/* exported
    getAvailableTableFilters,
*/


// Construct a dynamic API filter for the "issued by" field
function constructIssuedByFilter() {
    return {
        title: '{% trans "Issued By" %}',
        options: function() {
            let users = {};

            inventreeGet('{% url "api-user-list" %}', {}, {
                async: false,
                success: function(response) {
                    for (let user of response) {
                        users[user.pk] = {
                            key: user.pk,
                            value: user.username
                        };
                    }
                }
            });

            return users;
        }
    }
}

// Construct a dynamic API filter for the "project" field
function constructProjectCodeFilter() {
    return {
        title: '{% trans "Project Code" %}',
        options: function() {
            let project_codes = {};

            inventreeGet('{% url "api-project-code-list" %}', {}, {
                async: false,
                success: function(response) {
                    for (let code of response) {
                        project_codes[code.pk] = {
                            key: code.pk,
                            value: code.code
                        };
                    }
                }
            });

            return project_codes;
        }
    };
}


// Construct a filter for the "has project code" field
function constructHasProjectCodeFilter() {
    return {
        type: 'bool',
        title: '{% trans "Has project code" %}',
    };
}


// Reset a dictionary of filters for the attachment table
function getAttachmentFilters() {
    return {};
}


// Return a dictionary of filters for the return order table
function getReturnOrderFilters() {
    var filters = {
        status: {
            title: '{% trans "Order status" %}',
            options: returnOrderCodes
        },
        outstanding: {
            type: 'bool',
            title: '{% trans "Outstanding" %}',
        },
        overdue: {
            type: 'bool',
            title: '{% trans "Overdue" %}',
        },
        assigned_to_me: {
            type: 'bool',
            title: '{% trans "Assigned to me" %}',
        },
    };

    if (global_settings.PROJECT_CODES_ENABLED) {
        filters['has_project_code'] = constructHasProjectCodeFilter();
        filters['project_code'] = constructProjectCodeFilter();
    }

    return filters;
}


// Return a dictionary of filters for the return order line item table
function getReturnOrderLineItemFilters() {
    return {
        received: {
            type: 'bool',
            title: '{% trans "Received" %}',
        },
        outcome: {
            title: '{% trans "Outcome" %}',
            options: returnOrderLineItemCodes,
        }
    };
}


// Return a dictionary of filters for the variants table
function getVariantsTableFilters() {
    return {
        active: {
            type: 'bool',
            title: '{% trans "Active" %}',
        },
        template: {
            type: 'bool',
            title: '{% trans "Template" %}',
        },
        virtual: {
            type: 'bool',
            title: '{% trans "Virtual" %}',
        },
        trackable: {
            type: 'bool',
            title: '{% trans "Trackable" %}',
        },
    };
}


// Return a dictionary of filters for the BOM table
function getBOMTableFilters() {
    return {
        sub_part_trackable: {
            type: 'bool',
            title: '{% trans "Trackable Part" %}',
        },
        sub_part_assembly: {
            type: 'bool',
            title: '{% trans "Assembled Part" %}',
        },
        available_stock: {
            type: 'bool',
            title: '{% trans "Has Available Stock" %}',
        },
        on_order: {
            type: 'bool',
            title: '{% trans "On Order" %}',
        },
        validated: {
            type: 'bool',
            title: '{% trans "Validated" %}',
        },
        inherited: {
            type: 'bool',
            title: '{% trans "Gets inherited" %}',
        },
        allow_variants: {
            type: 'bool',
            title: '{% trans "Allow Variant Stock" %}',
        },
        optional: {
            type: 'bool',
            title: '{% trans "Optional" %}',
        },
        consumable: {
            type: 'bool',
            title: '{% trans "Consumable" %}',
        },
        has_pricing: {
            type: 'bool',
            title: '{% trans "Has Pricing" %}',
        },
    };
}


// Return a dictionary of filters for the "related parts" table
function getRelatedTableFilters() {
    return {};
}


// Return a dictionary of filters for the "used in" table
function getUsedInTableFilters() {
    return {
        'inherited': {
            type: 'bool',
            title: '{% trans "Gets inherited" %}',
        },
        'optional': {
            type: 'bool',
            title: '{% trans "Optional" %}',
        },
        'part_active': {
            type: 'bool',
            title: '{% trans "Active" %}',
        },
        'part_trackable': {
            type: 'bool',
            title: '{% trans "Trackable" %}',
        },
    };
}


// Return a dictionary of filters for the "stock location" table
function getStockLocationFilters() {
    return {
        cascade: {
            type: 'bool',
            title: '{% trans "Include sublocations" %}',
            description: '{% trans "Include locations" %}',
        },
        structural: {
            type: 'bool',
            title: '{% trans "Structural" %}',
        },
        external: {
            type: 'bool',
            title: '{% trans "External" %}',
        },
        location_type: {
            title: '{% trans "Location type" %}',
            options: function() {
                const locationTypes = {};

                inventreeGet('{% url "api-location-type-list" %}', {}, {
                    async: false,
                    success: function(response) {
                        for(const locationType of response) {
                            locationTypes[locationType.pk] = {
                                key: locationType.pk,
                                value: locationType.name,
                            }
                        }
                    }
                });

                return locationTypes;
            },
        },
        has_location_type: {
            type: 'bool',
            title: '{% trans "Has location type" %}'
        },
    };
}


// Return a dictionary of filters for the "part category" table
function getPartCategoryFilters() {
    return {
        cascade: {
            type: 'bool',
            title: '{% trans "Include subcategories" %}',
            description: '{% trans "Include subcategories" %}',
        },
        structural: {
            type: 'bool',
            title: '{% trans "Structural" %}',
        },
        starred: {
            type: 'bool',
            title: '{% trans "Subscribed" %}',
        },
    };
}


// Return a dictionary of filters for the "customer stock" table
function getCustomerStockFilters() {
    return {
        serialized: {
            type: 'bool',
            title: '{% trans "Is Serialized" %}',
        },
        serial_gte: {
            title: '{% trans "Serial number GTE" %}',
            description: '{% trans "Serial number greater than or equal to" %}',
        },
        serial_lte: {
            title: '{% trans "Serial number LTE" %}',
            description: '{% trans "Serial number less than or equal to" %}',
        },
        serial: {
            title: '{% trans "Serial number" %}',
            description: '{% trans "Serial number" %}',
        },
        batch: {
            title: '{% trans "Batch" %}',
            description: '{% trans "Batch code" %}',
        },
    };
}


// Return a dictionary of filters for the "stock" table
function getStockTableFilters() {
    var filters = {
        active: {
            type: 'bool',
            title: '{% trans "Active parts" %}',
            description: '{% trans "Show stock for active parts" %}',
        },
        assembly: {
            type: 'bool',
            title: '{% trans "Assembly" %}',
            description: '{% trans "Part is an assembly" %}',
        },
        allocated: {
            type: 'bool',
            title: '{% trans "Is allocated" %}',
            description: '{% trans "Item has been allocated" %}',
        },
        available: {
            type: 'bool',
            title: '{% trans "Available" %}',
            description: '{% trans "Stock is available for use" %}',
        },
        cascade: {
            type: 'bool',
            title: '{% trans "Include sublocations" %}',
            description: '{% trans "Include stock in sublocations" %}',
        },
        depleted: {
            type: 'bool',
            title: '{% trans "Depleted" %}',
            description: '{% trans "Show stock items which are depleted" %}',
        },
        in_stock: {
            type: 'bool',
            title: '{% trans "In Stock" %}',
            description: '{% trans "Show items which are in stock" %}',
        },
        is_building: {
            type: 'bool',
            title: '{% trans "In Production" %}',
            description: '{% trans "Show items which are in production" %}',
        },
        include_variants: {
            type: 'bool',
            title: '{% trans "Include Variants" %}',
            description: '{% trans "Include stock items for variant parts" %}',
        },
        installed: {
            type: 'bool',
            title: '{% trans "Installed" %}',
            description: '{% trans "Show stock items which are installed in another item" %}',
        },
        sent_to_customer: {
            type: 'bool',
            title: '{% trans "Sent to customer" %}',
            description: '{% trans "Show items which have been assigned to a customer" %}',
        },
        serialized: {
            type: 'bool',
            title: '{% trans "Is Serialized" %}',
        },
        serial: {
            title: '{% trans "Serial number" %}',
            description: '{% trans "Serial number" %}',
        },
        serial_gte: {
            title: '{% trans "Serial number GTE" %}',
            description: '{% trans "Serial number greater than or equal to" %}',
        },
        serial_lte: {
            title: '{% trans "Serial number LTE" %}',
            description: '{% trans "Serial number less than or equal to" %}',
        },
        status: {
            options: stockCodes,
            title: '{% trans "Stock status" %}',
            description: '{% trans "Stock status" %}',
        },
        has_batch: {
            title: '{% trans "Has batch code" %}',
            type: 'bool',
        },
        batch: {
            title: '{% trans "Batch" %}',
            description: '{% trans "Batch code" %}',
        },
        tracked: {
            title: '{% trans "Tracked" %}',
            description: '{% trans "Stock item is tracked by either batch code or serial number" %}',
            type: 'bool',
        },
        has_purchase_price: {
            type: 'bool',
            title: '{% trans "Has purchase price" %}',
            description: '{% trans "Show stock items which have a purchase price set" %}',
        },
        expiry_date_lte: {
            type: 'date',
            title: '{% trans "Expiry Date before" %}',
        },
        expiry_date_gte: {
            type: 'date',
            title: '{% trans "Expiry Date after" %}',
        },
        external: {
            type: 'bool',
            title: '{% trans "External Location" %}',
        }
    };

    // Optional filters if stock expiry functionality is enabled
    if (global_settings.STOCK_ENABLE_EXPIRY) {
        filters.expired = {
            type: 'bool',
            title: '{% trans "Expired" %}',
            description: '{% trans "Show stock items which have expired" %}',
        };

        filters.stale = {
            type: 'bool',
            title: '{% trans "Stale" %}',
            description: '{% trans "Show stock which is close to expiring" %}',
        };
    }

    return filters;
}


// Return a dictionary of filters for the "stock tests" table
function getStockTestTableFilters() {

    return {
        result: {
            type: 'bool',
            title: '{% trans "Test Passed" %}',
        },
        include_installed: {
            type: 'bool',
            title: '{% trans "Include Installed Items" %}',
        }
    };
}


// Return a dictionary of filters for the "stocktracking" table
function getStockTrackingTableFilters() {
    return {};
}


// Return a dictionary of filters for the "part tests" table
function getPartTestTemplateFilters() {
    return {
        required: {
            type: 'bool',
            title: '{% trans "Required" %}',
        },
        enabled: {
            type: 'bool',
            title: '{% trans "Enabled" %}',
        },
    };
}


// Return a dictionary of filters for the "plugins" table
function getPluginTableFilters() {
    return {
        active: {
            type: 'bool',
            title: '{% trans "Active" %}',
        },
        builtin: {
            type: 'bool',
            title: '{% trans "Builtin" %}',
        },
        sample: {
            type: 'bool',
            title: '{% trans "Sample" %}',
        },
        installed: {
            type: 'bool',
            title: '{% trans "Installed" %}'
        },
    };
}


// Return a dictionary of filters for the "build" table
function getBuildTableFilters() {

    let filters = {
        status: {
            title: '{% trans "Build status" %}',
            options: buildCodes,
        },
        active: {
            type: 'bool',
            title: '{% trans "Active" %}',
        },
        overdue: {
            type: 'bool',
            title: '{% trans "Overdue" %}',
        },
        assigned_to_me: {
            type: 'bool',
            title: '{% trans "Assigned to me" %}',
        },
        assigned_to: {
            title: '{% trans "Responsible" %}',
            options: function() {
                var ownersList = {};
                inventreeGet('{% url "api-owner-list" %}', {}, {
                    async: false,
                    success: function(response) {
                        for (var key in response) {
                            let owner = response[key];
                            ownersList[owner.pk] = {
                                key: owner.pk,
                                value: `${owner.name} (${owner.label})`,
                            };
                        }
                    }
                });
                return ownersList;
            },
        },
        issued_by: constructIssuedByFilter(),
    };

    if (global_settings.PROJECT_CODES_ENABLED) {
        filters['has_project_code'] = constructHasProjectCodeFilter();
        filters['project_code'] = constructProjectCodeFilter();
    }

    return filters;
}


function getBuildItemTableFilters() {
    return {};
}


// Return a dictionary of filters for the "build lines" table
function getBuildLineTableFilters() {
    return {
        allocated: {
            type: 'bool',
            title: '{% trans "Allocated" %}',
        },
        available: {
            type: 'bool',
            title: '{% trans "Available" %}',
        },
        tracked: {
            type: 'bool',
            title: '{% trans "Tracked" %}',
        },
        consumable: {
            type: 'bool',
            title: '{% trans "Consumable" %}',
        },
        optional: {
            type: 'bool',
            title: '{% trans "Optional" %}',
        },
    };
}


// Return a dictionary of filters for the "purchase order line item" table
function getPurchaseOrderLineItemFilters() {
    return {
        pending: {
            type: 'bool',
            title: '{% trans "Pending" %}',
        },
        received: {
            type: 'bool',
            title: '{% trans "Received" %}',
        },
        order_status: {
            title: '{% trans "Order status" %}',
            options: purchaseOrderCodes,
        },
    };
}


// Return a dictionary of filters for the "purchase order" table
function getPurchaseOrderFilters() {

    var filters = {
        status: {
            title: '{% trans "Order status" %}',
            options: purchaseOrderCodes,
        },
        outstanding: {
            type: 'bool',
            title: '{% trans "Outstanding" %}',
        },
        overdue: {
            type: 'bool',
            title: '{% trans "Overdue" %}',
        },
        assigned_to_me: {
            type: 'bool',
            title: '{% trans "Assigned to me" %}',
        },
    };

    if (global_settings.PROJECT_CODES_ENABLED) {
        filters['has_project_code'] = constructHasProjectCodeFilter();
        filters['project_code'] = constructProjectCodeFilter();
    }

    return filters;
}


// Return a dictionary of filters for the "sales order allocation" table
function getSalesOrderAllocationFilters() {
    return {
        outstanding: {
            type: 'bool',
            title: '{% trans "Outstanding" %}',
        }
    };
}


// Return a dictionary of filters for the "sales order" table
function getSalesOrderFilters() {
    var filters = {
        status: {
            title: '{% trans "Order status" %}',
            options: salesOrderCodes,
        },
        outstanding: {
            type: 'bool',
            title: '{% trans "Outstanding" %}',
        },
        overdue: {
            type: 'bool',
            title: '{% trans "Overdue" %}',
        },
        assigned_to_me: {
            type: 'bool',
            title: '{% trans "Assigned to me" %}',
        },
    };

    if (global_settings.PROJECT_CODES_ENABLED) {
        filters['has_project_code'] = constructHasProjectCodeFilter();
        filters['project_code'] = constructProjectCodeFilter();
    }

    return filters;
}


// Return a dictionary of filters for the "sales order line item" table
function getSalesOrderLineItemFilters() {
    return {
        completed: {
            type: 'bool',
            title: '{% trans "Completed" %}',
        },
    };
}


// Return a dictionary of filters for the "supplier part" table
function getSupplierPartFilters() {
    return {
        active: {
            type: 'bool',
            title: '{% trans "Active parts" %}',
        },
    };
}


// Return a dictionary of filters for the "part" table
function getPartTableFilters() {
    return {
        cascade: {
            type: 'bool',
            title: '{% trans "Include subcategories" %}',
            description: '{% trans "Include parts in subcategories" %}',
        },
        active: {
            type: 'bool',
            title: '{% trans "Active" %}',
            description: '{% trans "Show active parts" %}',
        },
        assembly: {
            type: 'bool',
            title: '{% trans "Assembly" %}',
        },
        unallocated_stock: {
            type: 'bool',
            title: '{% trans "Available stock" %}',
        },
        component: {
            type: 'bool',
            title: '{% trans "Component" %}',
        },
        has_units: {
            type: 'bool',
            title: '{% trans "Has Units" %}',
            description: '{% trans "Part has defined units" %}',
        },
        has_ipn: {
            type: 'bool',
            title: '{% trans "Has IPN" %}',
            description: '{% trans "Part has internal part number" %}',
        },
        has_stock: {
            type: 'bool',
            title: '{% trans "In stock" %}',
        },
        low_stock: {
            type: 'bool',
            title: '{% trans "Low stock" %}',
        },
        purchaseable: {
            type: 'bool',
            title: '{% trans "Purchasable" %}',
        },
        salable: {
            type: 'bool',
            title: '{% trans "Salable" %}',
        },
        starred: {
            type: 'bool',
            title: '{% trans "Subscribed" %}',
        },
        stocktake: {
            type: 'bool',
            title: '{% trans "Has stocktake entries" %}',
        },
        is_template: {
            type: 'bool',
            title: '{% trans "Template" %}',
        },
        trackable: {
            type: 'bool',
            title: '{% trans "Trackable" %}',
        },
        virtual: {
            type: 'bool',
            title: '{% trans "Virtual" %}',
        },
        has_pricing: {
            type: 'bool',
            title: '{% trans "Has Pricing" %}',
        },
    };
}


// Return a dictionary of filters for the "contact" table
function getContactFilters() {
    return {};
}


// Return a dictionary of filters for the "company" table
function getCompanyFilters() {
    return {
        is_manufacturer: {
            type: 'bool',
            title: '{% trans "Manufacturer" %}',
        },
        is_supplier: {
            type: 'bool',
            title: '{% trans "Supplier" %}',
        },
        is_customer: {
            type: 'bool',
            title: '{% trans "Customer" %}',
        },
    };
}


// Return a dictionary of filters for the "PartParameter" table
function getPartParameterFilters() {
    return {};
}


// Return a dictionary of filters for the "part parameter template" table
function getPartParameterTemplateFilters() {
    return {
        checkbox: {
            type: 'bool',
            title: '{% trans "Checkbox" %}',
        },
        has_choices: {
            type: 'bool',
            title: '{% trans "Has Choices" %}',
        },
        has_units: {
            type: 'bool',
            title: '{% trans "Has Units" %}',
        }
    };
}


// Return a dictionary of filters for the "parametric part" table
function getParametricPartTableFilters() {
    let filters = getPartTableFilters();

    return filters;
}


// Return a dictionary of filters for a given table, based on the name of the table
function getAvailableTableFilters(tableKey) {

    tableKey = tableKey.toLowerCase();

    switch (tableKey) {
    case 'attachments':
        return getAttachmentFilters();
    case 'build':
        return getBuildTableFilters();
    case 'builditems':
        return getBuildItemTableFilters();
    case 'buildlines':
        return getBuildLineTableFilters();
    case 'bom':
        return getBOMTableFilters();
    case 'category':
        return getPartCategoryFilters();
    case 'company':
        return getCompanyFilters();
    case 'contact':
        return getContactFilters();
    case 'customerstock':
        return getCustomerStockFilters();
    case 'location':
        return getStockLocationFilters();
    case 'parameters':
        return getParametricPartTableFilters();
    case 'part-parameters':
        return getPartParameterFilters();
    case 'part-parameter-templates':
        return getPartParameterTemplateFilters();
    case 'parts':
        return getPartTableFilters();
    case 'parttests':
        return getPartTestTemplateFilters();
    case 'plugins':
        return getPluginTableFilters();
    case 'purchaseorder':
        return getPurchaseOrderFilters();
    case 'purchaseorderlineitem':
        return getPurchaseOrderLineItemFilters();
    case 'related':
        return getRelatedTableFilters();
    case 'returnorder':
        return getReturnOrderFilters();
    case 'returnorderlineitem':
        return getReturnOrderLineItemFilters();
    case 'salesorder':
        return getSalesOrderFilters();
    case 'salesorderallocation':
        return getSalesOrderAllocationFilters();
    case 'salesorderlineitem':
        return getSalesOrderLineItemFilters();
    case 'stock':
        return getStockTableFilters();
    case 'stocktests':
        return getStockTestTableFilters();
    case 'stocktracking':
        return getStockTrackingTableFilters();
    case 'supplierpart':
        return getSupplierPartFilters();
    case 'usedin':
        return getUsedInTableFilters();
    case 'variants':
        return getVariantsTableFilters();
    default:
        console.warn(`No filters defined for table ${tableKey}`);
        return {};
    }
}
