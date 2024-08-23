



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


// Construct a dynamic API filter for an "owner"
function constructOwnerFilter(title) {
    return {
        title: title,
        options: function() {
            var ownersList = {};
            inventreeGet('/api/user/owner/', {}, {
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
    };
}

// Construct a dynamic API filter for the "project" field
function constructProjectCodeFilter() {
    return {
        title: 'Project Code',
        options: function() {
            let project_codes = {};

            inventreeGet('/api/project-code/', {}, {
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
        title: 'Has project code',
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
            title: 'Order status',
            options: returnOrderCodes
        },
        outstanding: {
            type: 'bool',
            title: 'Outstanding',
        },
        overdue: {
            type: 'bool',
            title: 'Overdue',
        },
        assigned_to_me: {
            type: 'bool',
            title: 'Assigned to me',
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
            title: 'Received',
        },
        outcome: {
            title: 'Outcome',
            options: returnOrderLineItemCodes,
        }
    };
}


// Return a dictionary of filters for the variants table
function getVariantsTableFilters() {
    return {
        active: {
            type: 'bool',
            title: 'Active',
        },
        template: {
            type: 'bool',
            title: 'Template',
        },
        virtual: {
            type: 'bool',
            title: 'Virtual',
        },
        testable: {
            type: 'bool',
            title: 'Testable',
        },
        trackable: {
            type: 'bool',
            title: 'Trackable',
        },
    };
}


// Return a dictionary of filters for the BOM table
function getBOMTableFilters() {
    return {
        sub_part_testable: {
            type: 'bool',
            title: 'Testable Part',
        },
        sub_part_trackable: {
            type: 'bool',
            title: 'Trackable Part',
        },
        sub_part_assembly: {
            type: 'bool',
            title: 'Assembled Part',
        },
        available_stock: {
            type: 'bool',
            title: 'Has Available Stock',
        },
        on_order: {
            type: 'bool',
            title: 'On Order',
        },
        validated: {
            type: 'bool',
            title: 'Validated',
        },
        inherited: {
            type: 'bool',
            title: 'Gets inherited',
        },
        allow_variants: {
            type: 'bool',
            title: 'Allow Variant Stock',
        },
        optional: {
            type: 'bool',
            title: 'Valgfri',
        },
        consumable: {
            type: 'bool',
            title: 'Forbrugsvare',
        },
        has_pricing: {
            type: 'bool',
            title: 'Has Pricing',
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
            title: 'Gets inherited',
        },
        'optional': {
            type: 'bool',
            title: 'Valgfri',
        },
        'part_active': {
            type: 'bool',
            title: 'Active',
        },
        'part_trackable': {
            type: 'bool',
            title: 'Trackable',
        },
    };
}


// Return a dictionary of filters for the "stock location" table
function getStockLocationFilters() {
    return {
        cascade: {
            type: 'bool',
            title: 'Include sublocations',
            description: 'Include locations',
        },
        structural: {
            type: 'bool',
            title: 'Structural',
        },
        external: {
            type: 'bool',
            title: 'External',
        },
        location_type: {
            title: 'Location type',
            options: function() {
                const locationTypes = {};

                inventreeGet('/api/stock/location-type/', {}, {
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
            title: 'Has location type'
        },
    };
}


// Return a dictionary of filters for the "part category" table
function getPartCategoryFilters() {
    return {
        cascade: {
            type: 'bool',
            title: 'Include subcategories',
            description: 'Include subcategories',
        },
        structural: {
            type: 'bool',
            title: 'Structural',
        },
        starred: {
            type: 'bool',
            title: 'Subscribed',
        },
    };
}


// Return a dictionary of filters for the "customer stock" table
function getCustomerStockFilters() {
    return {
        serialized: {
            type: 'bool',
            title: 'Is Serialized',
        },
        serial_gte: {
            title: 'Serial number GTE',
            description: 'Serial number greater than or equal to',
        },
        serial_lte: {
            title: 'Serial number LTE',
            description: 'Serial number less than or equal to',
        },
        serial: {
            title: 'Serial number',
            description: 'Serial number',
        },
        batch: {
            title: 'Batch',
            description: 'Batch code',
        },
    };
}


// Return a dictionary of filters for the "stock" table
function getStockTableFilters() {
    var filters = {
        active: {
            type: 'bool',
            title: 'Active parts',
            description: 'Show stock for active parts',
        },
        assembly: {
            type: 'bool',
            title: 'Assembly',
            description: 'Part is an assembly',
        },
        allocated: {
            type: 'bool',
            title: 'Is allocated',
            description: 'Item has been allocated',
        },
        available: {
            type: 'bool',
            title: 'Tilgængelig',
            description: 'Stock is available for use',
        },
        cascade: {
            type: 'bool',
            title: 'Include sublocations',
            description: 'Include stock in sublocations',
        },
        depleted: {
            type: 'bool',
            title: 'Depleted',
            description: 'Show stock items which are depleted',
        },
        in_stock: {
            type: 'bool',
            title: 'In Stock',
            description: 'Show items which are in stock',
        },
        is_building: {
            type: 'bool',
            title: 'In Production',
            description: 'Show items which are in production',
        },
        include_variants: {
            type: 'bool',
            title: 'Include Variants',
            description: 'Include stock items for variant parts',
        },
        installed: {
            type: 'bool',
            title: 'Installed',
            description: 'Show stock items which are installed in another item',
        },
        sent_to_customer: {
            type: 'bool',
            title: 'Sendt til kunde',
            description: 'Show items which have been assigned to a customer',
        },
        serialized: {
            type: 'bool',
            title: 'Is Serialized',
        },
        serial: {
            title: 'Serial number',
            description: 'Serial number',
        },
        serial_gte: {
            title: 'Serial number GTE',
            description: 'Serial number greater than or equal to',
        },
        serial_lte: {
            title: 'Serial number LTE',
            description: 'Serial number less than or equal to',
        },
        status: {
            options: stockCodes,
            title: 'Stock status',
            description: 'Stock status',
        },
        has_batch: {
            title: 'Has batch code',
            type: 'bool',
        },
        batch: {
            title: 'Batch',
            description: 'Batch code',
        },
        tracked: {
            title: 'Sporet',
            description: 'Stock item is tracked by either batch code or serial number',
            type: 'bool',
        },
        has_purchase_price: {
            type: 'bool',
            title: 'Has purchase price',
            description: 'Show stock items which have a purchase price set',
        },
        expiry_date_lte: {
            type: 'date',
            title: 'Expiry Date before',
        },
        expiry_date_gte: {
            type: 'date',
            title: 'Expiry Date after',
        },
        external: {
            type: 'bool',
            title: 'External Location',
        }
    };

    // Optional filters if stock expiry functionality is enabled
    if (global_settings.STOCK_ENABLE_EXPIRY) {
        filters.expired = {
            type: 'bool',
            title: 'Expired',
            description: 'Show stock items which have expired',
        };

        filters.stale = {
            type: 'bool',
            title: 'Stale',
            description: 'Show stock which is close to expiring',
        };
    }

    return filters;
}


// Return a dictionary of filters for the "stock tests" table
function getStockTestTableFilters() {

    return {
        result: {
            type: 'bool',
            title: 'Test Passed',
        },
        include_installed: {
            type: 'bool',
            title: 'Include Installed Items',
        }
    };
}

// Return a dictionary of filters for the "test statistics" table
function getTestStatisticsTableFilters() {

    return {
        finished_datetime_after: {
            type: 'date',
            title: 'Interval start',
        },
        finished_datetime_before: {
            type: 'date',
            title: 'Interval end',
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
            title: 'Required',
        },
        enabled: {
            type: 'bool',
            title: 'Enabled',
        },
    };
}


// Return a dictionary of filters for the "plugins" table
function getPluginTableFilters() {
    return {
        active: {
            type: 'bool',
            title: 'Active',
        },
        builtin: {
            type: 'bool',
            title: 'Builtin',
        },
        sample: {
            type: 'bool',
            title: 'Sample',
        },
        installed: {
            type: 'bool',
            title: 'Installed'
        },
    };
}


// Return a dictionary of filters for the "build" table
function getBuildTableFilters() {

    let filters = {
        status: {
            title: 'Build status',
            options: buildCodes,
        },
        active: {
            type: 'bool',
            title: 'Active',
        },
        overdue: {
            type: 'bool',
            title: 'Overdue',
        },
        assigned_to_me: {
            type: 'bool',
            title: 'Assigned to me',
        },
        assigned_to: constructOwnerFilter('Ansvarlig'),
        issued_by: constructOwnerFilter('Issued By'),
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
            title: 'Allokeret',
        },
        available: {
            type: 'bool',
            title: 'Tilgængelig',
        },
        tracked: {
            type: 'bool',
            title: 'Sporet',
        },
        consumable: {
            type: 'bool',
            title: 'Forbrugsvare',
        },
        optional: {
            type: 'bool',
            title: 'Valgfri',
        },
    };
}


// Return a dictionary of filters for the "purchase order line item" table
function getPurchaseOrderLineItemFilters() {
    return {
        pending: {
            type: 'bool',
            title: 'Afventende',
        },
        received: {
            type: 'bool',
            title: 'Received',
        },
        order_status: {
            title: 'Order status',
            options: purchaseOrderCodes,
        },
    };
}


// Return a dictionary of filters for the "purchase order" table
function getPurchaseOrderFilters() {

    var filters = {
        status: {
            title: 'Order status',
            options: purchaseOrderCodes,
        },
        outstanding: {
            type: 'bool',
            title: 'Outstanding',
        },
        overdue: {
            type: 'bool',
            title: 'Overdue',
        },
        assigned_to_me: {
            type: 'bool',
            title: 'Assigned to me',
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
            title: 'Outstanding',
        }
    };
}


// Return a dictionary of filters for the "sales order" table
function getSalesOrderFilters() {
    var filters = {
        status: {
            title: 'Order status',
            options: salesOrderCodes,
        },
        outstanding: {
            type: 'bool',
            title: 'Outstanding',
        },
        overdue: {
            type: 'bool',
            title: 'Overdue',
        },
        assigned_to_me: {
            type: 'bool',
            title: 'Assigned to me',
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
            title: 'Completed',
        },
    };
}


// Return a dictionary of filters for the "supplier part" table
function getSupplierPartFilters() {
    return {
        active: {
            type: 'bool',
            title: 'Active parts',
        },
    };
}


// Return a dictionary of filters for the "part" table
function getPartTableFilters() {
    return {
        cascade: {
            type: 'bool',
            title: 'Include subcategories',
            description: 'Include parts in subcategories',
        },
        active: {
            type: 'bool',
            title: 'Active',
            description: 'Show active parts',
        },
        locked: {
            type: 'bool',
            title: 'Locked',
            description: 'Show locked parts',
        },
        assembly: {
            type: 'bool',
            title: 'Assembly',
        },
        unallocated_stock: {
            type: 'bool',
            title: 'Available stock',
        },
        component: {
            type: 'bool',
            title: 'Component',
        },
        has_units: {
            type: 'bool',
            title: 'Has Units',
            description: 'Part has defined units',
        },
        has_ipn: {
            type: 'bool',
            title: 'Has IPN',
            description: 'Part has internal part number',
        },
        has_stock: {
            type: 'bool',
            title: 'In stock',
        },
        low_stock: {
            type: 'bool',
            title: 'Low stock',
        },
        purchaseable: {
            type: 'bool',
            title: 'Purchasable',
        },
        salable: {
            type: 'bool',
            title: 'Salable',
        },
        starred: {
            type: 'bool',
            title: 'Subscribed',
        },
        stocktake: {
            type: 'bool',
            title: 'Has stocktake entries',
        },
        is_template: {
            type: 'bool',
            title: 'Template',
        },
        testable: {
            type: 'bool',
            title: 'Testable',
        },
        trackable: {
            type: 'bool',
            title: 'Trackable',
        },
        virtual: {
            type: 'bool',
            title: 'Virtual',
        },
        has_pricing: {
            type: 'bool',
            title: 'Has Pricing',
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
        active: {
            type: 'bool',
            title: 'Active'
        },
        is_manufacturer: {
            type: 'bool',
            title: 'Manufacturer',
        },
        is_supplier: {
            type: 'bool',
            title: 'Supplier',
        },
        is_customer: {
            type: 'bool',
            title: 'Customer',
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
            title: 'Checkbox',
        },
        has_choices: {
            type: 'bool',
            title: 'Has Choices',
        },
        has_units: {
            type: 'bool',
            title: 'Has Units',
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
    case 'buildteststatistics':
        return getTestStatisticsTableFilters();
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
    case 'partteststatistics':
        return getTestStatisticsTableFilters();
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
