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
        title: '{% jstrans "Issued By" %}',
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
        title: '{% jstrans "Project Code" %}',
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
        title: '{% jstrans "Has project code" %}',
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
            title: '{% jstrans "Order status" %}',
            options: returnOrderCodes
        },
        outstanding: {
            type: 'bool',
            title: '{% jstrans "Outstanding" %}',
        },
        overdue: {
            type: 'bool',
            title: '{% jstrans "Overdue" %}',
        },
        assigned_to_me: {
            type: 'bool',
            title: '{% jstrans "Assigned to me" %}',
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
            title: '{% jstrans "Received" %}',
        },
        outcome: {
            title: '{% jstrans "Outcome" %}',
            options: returnOrderLineItemCodes,
        }
    };
}


// Return a dictionary of filters for the variants table
function getVariantsTableFilters() {
    return {
        active: {
            type: 'bool',
            title: '{% jstrans "Active" %}',
        },
        template: {
            type: 'bool',
            title: '{% jstrans "Template" %}',
        },
        virtual: {
            type: 'bool',
            title: '{% jstrans "Virtual" %}',
        },
        trackable: {
            type: 'bool',
            title: '{% jstrans "Trackable" %}',
        },
    };
}


// Return a dictionary of filters for the BOM table
function getBOMTableFilters() {
    return {
        sub_part_trackable: {
            type: 'bool',
            title: '{% jstrans "Trackable Part" %}',
        },
        sub_part_assembly: {
            type: 'bool',
            title: '{% jstrans "Assembled Part" %}',
        },
        available_stock: {
            type: 'bool',
            title: '{% jstrans "Has Available Stock" %}',
        },
        on_order: {
            type: 'bool',
            title: '{% jstrans "On Order" %}',
        },
        validated: {
            type: 'bool',
            title: '{% jstrans "Validated" %}',
        },
        inherited: {
            type: 'bool',
            title: '{% jstrans "Gets inherited" %}',
        },
        allow_variants: {
            type: 'bool',
            title: '{% jstrans "Allow Variant Stock" %}',
        },
        optional: {
            type: 'bool',
            title: '{% jstrans "Optional" %}',
        },
        consumable: {
            type: 'bool',
            title: '{% jstrans "Consumable" %}',
        },
        has_pricing: {
            type: 'bool',
            title: '{% jstrans "Has Pricing" %}',
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
            title: '{% jstrans "Gets inherited" %}',
        },
        'optional': {
            type: 'bool',
            title: '{% jstrans "Optional" %}',
        },
        'part_active': {
            type: 'bool',
            title: '{% jstrans "Active" %}',
        },
        'part_trackable': {
            type: 'bool',
            title: '{% jstrans "Trackable" %}',
        },
    };
}


// Return a dictionary of filters for the "stock location" table
function getStockLocationFilters() {
    return {
        cascade: {
            type: 'bool',
            title: '{% jstrans "Include sublocations" %}',
            description: '{% jstrans "Include locations" %}',
        },
        structural: {
            type: 'bool',
            title: '{% jstrans "Structural" %}',
        },
        external: {
            type: 'bool',
            title: '{% jstrans "External" %}',
        },
        location_type: {
            title: '{% jstrans "Location type" %}',
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
            title: '{% jstrans "Has location type" %}'
        },
    };
}


// Return a dictionary of filters for the "part category" table
function getPartCategoryFilters() {
    return {
        cascade: {
            type: 'bool',
            title: '{% jstrans "Include subcategories" %}',
            description: '{% jstrans "Include subcategories" %}',
        },
        structural: {
            type: 'bool',
            title: '{% jstrans "Structural" %}',
        },
        starred: {
            type: 'bool',
            title: '{% jstrans "Subscribed" %}',
        },
    };
}


// Return a dictionary of filters for the "customer stock" table
function getCustomerStockFilters() {
    return {
        serialized: {
            type: 'bool',
            title: '{% jstrans "Is Serialized" %}',
        },
        serial_gte: {
            title: '{% jstrans "Serial number GTE" %}',
            description: '{% jstrans "Serial number greater than or equal to" %}',
        },
        serial_lte: {
            title: '{% jstrans "Serial number LTE" %}',
            description: '{% jstrans "Serial number less than or equal to" %}',
        },
        serial: {
            title: '{% jstrans "Serial number" %}',
            description: '{% jstrans "Serial number" %}',
        },
        batch: {
            title: '{% jstrans "Batch" %}',
            description: '{% jstrans "Batch code" %}',
        },
    };
}


// Return a dictionary of filters for the "stock" table
function getStockTableFilters() {
    var filters = {
        active: {
            type: 'bool',
            title: '{% jstrans "Active parts" %}',
            description: '{% jstrans "Show stock for active parts" %}',
        },
        assembly: {
            type: 'bool',
            title: '{% jstrans "Assembly" %}',
            description: '{% jstrans "Part is an assembly" %}',
        },
        allocated: {
            type: 'bool',
            title: '{% jstrans "Is allocated" %}',
            description: '{% jstrans "Item has been allocated" %}',
        },
        available: {
            type: 'bool',
            title: '{% jstrans "Available" %}',
            description: '{% jstrans "Stock is available for use" %}',
        },
        cascade: {
            type: 'bool',
            title: '{% jstrans "Include sublocations" %}',
            description: '{% jstrans "Include stock in sublocations" %}',
        },
        depleted: {
            type: 'bool',
            title: '{% jstrans "Depleted" %}',
            description: '{% jstrans "Show stock items which are depleted" %}',
        },
        in_stock: {
            type: 'bool',
            title: '{% jstrans "In Stock" %}',
            description: '{% jstrans "Show items which are in stock" %}',
        },
        is_building: {
            type: 'bool',
            title: '{% jstrans "In Production" %}',
            description: '{% jstrans "Show items which are in production" %}',
        },
        include_variants: {
            type: 'bool',
            title: '{% jstrans "Include Variants" %}',
            description: '{% jstrans "Include stock items for variant parts" %}',
        },
        installed: {
            type: 'bool',
            title: '{% jstrans "Installed" %}',
            description: '{% jstrans "Show stock items which are installed in another item" %}',
        },
        sent_to_customer: {
            type: 'bool',
            title: '{% jstrans "Sent to customer" %}',
            description: '{% jstrans "Show items which have been assigned to a customer" %}',
        },
        serialized: {
            type: 'bool',
            title: '{% jstrans "Is Serialized" %}',
        },
        serial: {
            title: '{% jstrans "Serial number" %}',
            description: '{% jstrans "Serial number" %}',
        },
        serial_gte: {
            title: '{% jstrans "Serial number GTE" %}',
            description: '{% jstrans "Serial number greater than or equal to" %}',
        },
        serial_lte: {
            title: '{% jstrans "Serial number LTE" %}',
            description: '{% jstrans "Serial number less than or equal to" %}',
        },
        status: {
            options: stockCodes,
            title: '{% jstrans "Stock status" %}',
            description: '{% jstrans "Stock status" %}',
        },
        has_batch: {
            title: '{% jstrans "Has batch code" %}',
            type: 'bool',
        },
        batch: {
            title: '{% jstrans "Batch" %}',
            description: '{% jstrans "Batch code" %}',
        },
        tracked: {
            title: '{% jstrans "Tracked" %}',
            description: '{% jstrans "Stock item is tracked by either batch code or serial number" %}',
            type: 'bool',
        },
        has_purchase_price: {
            type: 'bool',
            title: '{% jstrans "Has purchase price" %}',
            description: '{% jstrans "Show stock items which have a purchase price set" %}',
        },
        expiry_date_lte: {
            type: 'date',
            title: '{% jstrans "Expiry Date before" %}',
        },
        expiry_date_gte: {
            type: 'date',
            title: '{% jstrans "Expiry Date after" %}',
        },
        external: {
            type: 'bool',
            title: '{% jstrans "External Location" %}',
        }
    };

    // Optional filters if stock expiry functionality is enabled
    if (global_settings.STOCK_ENABLE_EXPIRY) {
        filters.expired = {
            type: 'bool',
            title: '{% jstrans "Expired" %}',
            description: '{% jstrans "Show stock items which have expired" %}',
        };

        filters.stale = {
            type: 'bool',
            title: '{% jstrans "Stale" %}',
            description: '{% jstrans "Show stock which is close to expiring" %}',
        };
    }

    return filters;
}


// Return a dictionary of filters for the "stock tests" table
function getStockTestTableFilters() {

    return {
        result: {
            type: 'bool',
            title: '{% jstrans "Test Passed" %}',
        },
        include_installed: {
            type: 'bool',
            title: '{% jstrans "Include Installed Items" %}',
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
            title: '{% jstrans "Required" %}',
        },
    };
}


// Return a dictionary of filters for the "plugins" table
function getPluginTableFilters() {
    return {
        active: {
            type: 'bool',
            title: '{% jstrans "Active" %}',
        },
        builtin: {
            type: 'bool',
            title: '{% jstrans "Builtin" %}',
        },
        sample: {
            type: 'bool',
            title: '{% jstrans "Sample" %}',
        },
        installed: {
            type: 'bool',
            title: '{% jstrans "Installed" %}'
        },
    };
}


// Return a dictionary of filters for the "build" table
function getBuildTableFilters() {

    let filters = {
        status: {
            title: '{% jstrans "Build status" %}',
            options: buildCodes,
        },
        active: {
            type: 'bool',
            title: '{% jstrans "Active" %}',
        },
        overdue: {
            type: 'bool',
            title: '{% jstrans "Overdue" %}',
        },
        assigned_to_me: {
            type: 'bool',
            title: '{% jstrans "Assigned to me" %}',
        },
        assigned_to: {
            title: '{% jstrans "Responsible" %}',
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
            title: '{% jstrans "Allocated" %}',
        },
        available: {
            type: 'bool',
            title: '{% jstrans "Available" %}',
        },
        tracked: {
            type: 'bool',
            title: '{% jstrans "Tracked" %}',
        },
        consumable: {
            type: 'bool',
            title: '{% jstrans "Consumable" %}',
        },
        optional: {
            type: 'bool',
            title: '{% jstrans "Optional" %}',
        },
    };
}


// Return a dictionary of filters for the "purchase order line item" table
function getPurchaseOrderLineItemFilters() {
    return {
        pending: {
            type: 'bool',
            title: '{% jstrans "Pending" %}',
        },
        received: {
            type: 'bool',
            title: '{% jstrans "Received" %}',
        },
        order_status: {
            title: '{% jstrans "Order status" %}',
            options: purchaseOrderCodes,
        },
    };
}


// Return a dictionary of filters for the "purchase order" table
function getPurchaseOrderFilters() {

    var filters = {
        status: {
            title: '{% jstrans "Order status" %}',
            options: purchaseOrderCodes,
        },
        outstanding: {
            type: 'bool',
            title: '{% jstrans "Outstanding" %}',
        },
        overdue: {
            type: 'bool',
            title: '{% jstrans "Overdue" %}',
        },
        assigned_to_me: {
            type: 'bool',
            title: '{% jstrans "Assigned to me" %}',
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
            title: '{% jstrans "Outstanding" %}',
        }
    };
}


// Return a dictionary of filters for the "sales order" table
function getSalesOrderFilters() {
    var filters = {
        status: {
            title: '{% jstrans "Order status" %}',
            options: salesOrderCodes,
        },
        outstanding: {
            type: 'bool',
            title: '{% jstrans "Outstanding" %}',
        },
        overdue: {
            type: 'bool',
            title: '{% jstrans "Overdue" %}',
        },
        assigned_to_me: {
            type: 'bool',
            title: '{% jstrans "Assigned to me" %}',
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
            title: '{% jstrans "Completed" %}',
        },
    };
}


// Return a dictionary of filters for the "supplier part" table
function getSupplierPartFilters() {
    return {
        active: {
            type: 'bool',
            title: '{% jstrans "Active parts" %}',
        },
    };
}


// Return a dictionary of filters for the "part" table
function getPartTableFilters() {
    return {
        cascade: {
            type: 'bool',
            title: '{% jstrans "Include subcategories" %}',
            description: '{% jstrans "Include parts in subcategories" %}',
        },
        active: {
            type: 'bool',
            title: '{% jstrans "Active" %}',
            description: '{% jstrans "Show active parts" %}',
        },
        assembly: {
            type: 'bool',
            title: '{% jstrans "Assembly" %}',
        },
        unallocated_stock: {
            type: 'bool',
            title: '{% jstrans "Available stock" %}',
        },
        component: {
            type: 'bool',
            title: '{% jstrans "Component" %}',
        },
        has_units: {
            type: 'bool',
            title: '{% jstrans "Has Units" %}',
            description: '{% jstrans "Part has defined units" %}',
        },
        has_ipn: {
            type: 'bool',
            title: '{% jstrans "Has IPN" %}',
            description: '{% jstrans "Part has internal part number" %}',
        },
        has_stock: {
            type: 'bool',
            title: '{% jstrans "In stock" %}',
        },
        low_stock: {
            type: 'bool',
            title: '{% jstrans "Low stock" %}',
        },
        purchaseable: {
            type: 'bool',
            title: '{% jstrans "Purchasable" %}',
        },
        salable: {
            type: 'bool',
            title: '{% jstrans "Salable" %}',
        },
        starred: {
            type: 'bool',
            title: '{% jstrans "Subscribed" %}',
        },
        stocktake: {
            type: 'bool',
            title: '{% jstrans "Has stocktake entries" %}',
        },
        is_template: {
            type: 'bool',
            title: '{% jstrans "Template" %}',
        },
        trackable: {
            type: 'bool',
            title: '{% jstrans "Trackable" %}',
        },
        virtual: {
            type: 'bool',
            title: '{% jstrans "Virtual" %}',
        },
        has_pricing: {
            type: 'bool',
            title: '{% jstrans "Has Pricing" %}',
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
            title: '{% jstrans "Manufacturer" %}',
        },
        is_supplier: {
            type: 'bool',
            title: '{% jstrans "Supplier" %}',
        },
        is_customer: {
            type: 'bool',
            title: '{% jstrans "Customer" %}',
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
            title: '{% jstrans "Checkbox" %}',
        },
        has_choices: {
            type: 'bool',
            title: '{% jstrans "Has Choices" %}',
        },
        has_units: {
            type: 'bool',
            title: '{% jstrans "Has Units" %}',
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
