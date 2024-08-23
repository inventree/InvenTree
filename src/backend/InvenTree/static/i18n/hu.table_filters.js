



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
        title: 'Projektszám',
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
        title: 'Van projektszáma',
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
            title: 'Rendelés állapota',
            options: returnOrderCodes
        },
        outstanding: {
            type: 'bool',
            title: 'Kintlévő',
        },
        overdue: {
            type: 'bool',
            title: 'Késésben',
        },
        assigned_to_me: {
            type: 'bool',
            title: 'Hozzám rendelt',
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
            title: 'Beérkezett',
        },
        outcome: {
            title: 'Kimenetel',
            options: returnOrderLineItemCodes,
        }
    };
}


// Return a dictionary of filters for the variants table
function getVariantsTableFilters() {
    return {
        active: {
            type: 'bool',
            title: 'Aktív',
        },
        template: {
            type: 'bool',
            title: 'Sablon',
        },
        virtual: {
            type: 'bool',
            title: 'Virtuális',
        },
        testable: {
            type: 'bool',
            title: 'Testable',
        },
        trackable: {
            type: 'bool',
            title: 'Követésre kötelezett',
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
            title: 'Követésre kötelezett',
        },
        sub_part_assembly: {
            type: 'bool',
            title: 'Gyártmány alkatrész',
        },
        available_stock: {
            type: 'bool',
            title: 'Van elérhető készlete',
        },
        on_order: {
            type: 'bool',
            title: 'Rendelve',
        },
        validated: {
            type: 'bool',
            title: 'Jóváhagyva',
        },
        inherited: {
            type: 'bool',
            title: 'Öröklődött',
        },
        allow_variants: {
            type: 'bool',
            title: 'Készlet változatok engedélyezése',
        },
        optional: {
            type: 'bool',
            title: 'Opcionális',
        },
        consumable: {
            type: 'bool',
            title: 'Fogyóeszköz',
        },
        has_pricing: {
            type: 'bool',
            title: 'Van árazás',
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
            title: 'Öröklődött',
        },
        'optional': {
            type: 'bool',
            title: 'Opcionális',
        },
        'part_active': {
            type: 'bool',
            title: 'Aktív',
        },
        'part_trackable': {
            type: 'bool',
            title: 'Követésre kötelezett',
        },
    };
}


// Return a dictionary of filters for the "stock location" table
function getStockLocationFilters() {
    return {
        cascade: {
            type: 'bool',
            title: 'Alhelyekkel együtt',
            description: 'Helyekkel együtt',
        },
        structural: {
            type: 'bool',
            title: 'Szerkezeti',
        },
        external: {
            type: 'bool',
            title: 'Külső',
        },
        location_type: {
            title: 'Helyszín típusa',
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
            title: 'Van készlethely típusa'
        },
    };
}


// Return a dictionary of filters for the "part category" table
function getPartCategoryFilters() {
    return {
        cascade: {
            type: 'bool',
            title: 'Alkategóriákkal együtt',
            description: 'Alkategóriákkal együtt',
        },
        structural: {
            type: 'bool',
            title: 'Szerkezeti',
        },
        starred: {
            type: 'bool',
            title: 'Értesítés beállítva',
        },
    };
}


// Return a dictionary of filters for the "customer stock" table
function getCustomerStockFilters() {
    return {
        serialized: {
            type: 'bool',
            title: 'Sorozatszámos',
        },
        serial_gte: {
            title: 'Sorozatszám gt=',
            description: 'Sorozatszám nagyobb vagy egyenlő mint',
        },
        serial_lte: {
            title: 'Sorozatszám lt=',
            description: 'Sorozatszám kisebb vagy egyenlő mint',
        },
        serial: {
            title: 'Sorozatszám',
            description: 'Sorozatszám',
        },
        batch: {
            title: 'Köteg',
            description: 'Batch kód',
        },
    };
}


// Return a dictionary of filters for the "stock" table
function getStockTableFilters() {
    var filters = {
        active: {
            type: 'bool',
            title: 'Aktív alkatrész',
            description: 'Aktív alkatrészek készletének megjelenítése',
        },
        assembly: {
            type: 'bool',
            title: 'Gyártmány',
            description: 'Az alkatrész egy gyártmány',
        },
        allocated: {
            type: 'bool',
            title: 'Lefoglalt',
            description: 'Az tétel lefoglalásra került',
        },
        available: {
            type: 'bool',
            title: 'Elérhető',
            description: 'Felhasználható készlet',
        },
        cascade: {
            type: 'bool',
            title: 'Alhelyekkel együtt',
            description: 'Alhelyeken lévő készlettel együtt',
        },
        depleted: {
            type: 'bool',
            title: 'Kimerült',
            description: 'Kimerült készlet tételek megjelenítése',
        },
        in_stock: {
            type: 'bool',
            title: 'Készleten',
            description: 'Készleten lévő tételek megjelenítése',
        },
        is_building: {
            type: 'bool',
            title: 'Gyártásban',
            description: 'Gyártásban lévő tételek megjelenítése',
        },
        include_variants: {
            type: 'bool',
            title: 'Változatokkal együtt',
            description: 'Alkatrészváltozatok készletével együtt',
        },
        installed: {
            type: 'bool',
            title: 'Beépítve',
            description: 'Másik tételbe beépült tételek mutatása',
        },
        sent_to_customer: {
            type: 'bool',
            title: 'Vevőnek kiszállítva',
            description: 'Készlet tételek melyek hozzá vannak rendelve egy vevőhöz',
        },
        serialized: {
            type: 'bool',
            title: 'Sorozatszámos',
        },
        serial: {
            title: 'Sorozatszám',
            description: 'Sorozatszám',
        },
        serial_gte: {
            title: 'Sorozatszám gt=',
            description: 'Sorozatszám nagyobb vagy egyenlő mint',
        },
        serial_lte: {
            title: 'Sorozatszám lt=',
            description: 'Sorozatszám kisebb vagy egyenlő mint',
        },
        status: {
            options: stockCodes,
            title: 'Készlet állapota',
            description: 'Készlet állapota',
        },
        has_batch: {
            title: 'Van batch kódja',
            type: 'bool',
        },
        batch: {
            title: 'Köteg',
            description: 'Batch kód',
        },
        tracked: {
            title: 'Követett',
            description: 'Követett készlet tétel sorozatszámmal vagy batch kóddal',
            type: 'bool',
        },
        has_purchase_price: {
            type: 'bool',
            title: 'Van beszerzési ára',
            description: 'Beszerzési árral rendelkező készlet tételek megjelenítése',
        },
        expiry_date_lte: {
            type: 'date',
            title: 'Lejárat előtt',
        },
        expiry_date_gte: {
            type: 'date',
            title: 'Lejárat után',
        },
        external: {
            type: 'bool',
            title: 'Külső hely',
        }
    };

    // Optional filters if stock expiry functionality is enabled
    if (global_settings.STOCK_ENABLE_EXPIRY) {
        filters.expired = {
            type: 'bool',
            title: 'Lejárt',
            description: 'Lejárt készlet tételek megjelenítése',
        };

        filters.stale = {
            type: 'bool',
            title: 'Állott',
            description: 'Hamarosan lejáró készlet tételek megjelenítése',
        };
    }

    return filters;
}


// Return a dictionary of filters for the "stock tests" table
function getStockTestTableFilters() {

    return {
        result: {
            type: 'bool',
            title: 'Teszten megfelelt',
        },
        include_installed: {
            type: 'bool',
            title: 'Beépített tételekkel együtt',
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
            title: 'Kötelező',
        },
        enabled: {
            type: 'bool',
            title: 'Engedélyezve',
        },
    };
}


// Return a dictionary of filters for the "plugins" table
function getPluginTableFilters() {
    return {
        active: {
            type: 'bool',
            title: 'Aktív',
        },
        builtin: {
            type: 'bool',
            title: 'Beépített',
        },
        sample: {
            type: 'bool',
            title: 'Minta',
        },
        installed: {
            type: 'bool',
            title: 'Beépítve'
        },
    };
}


// Return a dictionary of filters for the "build" table
function getBuildTableFilters() {

    let filters = {
        status: {
            title: 'Gyártási állapot',
            options: buildCodes,
        },
        active: {
            type: 'bool',
            title: 'Aktív',
        },
        overdue: {
            type: 'bool',
            title: 'Késésben',
        },
        assigned_to_me: {
            type: 'bool',
            title: 'Hozzám rendelt',
        },
        assigned_to: constructOwnerFilter('Felelős'),
        issued_by: constructOwnerFilter('Kiállította'),
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
            title: 'Lefoglalva',
        },
        available: {
            type: 'bool',
            title: 'Elérhető',
        },
        tracked: {
            type: 'bool',
            title: 'Követett',
        },
        consumable: {
            type: 'bool',
            title: 'Fogyóeszköz',
        },
        optional: {
            type: 'bool',
            title: 'Opcionális',
        },
    };
}


// Return a dictionary of filters for the "purchase order line item" table
function getPurchaseOrderLineItemFilters() {
    return {
        pending: {
            type: 'bool',
            title: 'Függőben',
        },
        received: {
            type: 'bool',
            title: 'Beérkezett',
        },
        order_status: {
            title: 'Rendelés állapota',
            options: purchaseOrderCodes,
        },
    };
}


// Return a dictionary of filters for the "purchase order" table
function getPurchaseOrderFilters() {

    var filters = {
        status: {
            title: 'Rendelés állapota',
            options: purchaseOrderCodes,
        },
        outstanding: {
            type: 'bool',
            title: 'Kintlévő',
        },
        overdue: {
            type: 'bool',
            title: 'Késésben',
        },
        assigned_to_me: {
            type: 'bool',
            title: 'Hozzám rendelt',
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
            title: 'Kintlévő',
        }
    };
}


// Return a dictionary of filters for the "sales order" table
function getSalesOrderFilters() {
    var filters = {
        status: {
            title: 'Rendelés állapota',
            options: salesOrderCodes,
        },
        outstanding: {
            type: 'bool',
            title: 'Kintlévő',
        },
        overdue: {
            type: 'bool',
            title: 'Késésben',
        },
        assigned_to_me: {
            type: 'bool',
            title: 'Hozzám rendelt',
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
            title: 'Kész',
        },
    };
}


// Return a dictionary of filters for the "supplier part" table
function getSupplierPartFilters() {
    return {
        active: {
            type: 'bool',
            title: 'Aktív alkatrész',
        },
    };
}


// Return a dictionary of filters for the "part" table
function getPartTableFilters() {
    return {
        cascade: {
            type: 'bool',
            title: 'Alkategóriákkal együtt',
            description: 'Alkategóriákkal együtt',
        },
        active: {
            type: 'bool',
            title: 'Aktív',
            description: 'Aktív alkatrészek megjelenítése',
        },
        locked: {
            type: 'bool',
            title: 'Locked',
            description: 'Show locked parts',
        },
        assembly: {
            type: 'bool',
            title: 'Gyártmány',
        },
        unallocated_stock: {
            type: 'bool',
            title: 'Elérhető',
        },
        component: {
            type: 'bool',
            title: 'Összetevő',
        },
        has_units: {
            type: 'bool',
            title: 'Van mértékegysége',
            description: 'Az alkatrésznek van megadva mértékegysége',
        },
        has_ipn: {
            type: 'bool',
            title: 'Van IPN-je',
            description: 'Van belső cikkszáma',
        },
        has_stock: {
            type: 'bool',
            title: 'Készleten',
        },
        low_stock: {
            type: 'bool',
            title: 'Alacsony készlet',
        },
        purchaseable: {
            type: 'bool',
            title: 'Beszerezhető',
        },
        salable: {
            type: 'bool',
            title: 'Értékesíthető',
        },
        starred: {
            type: 'bool',
            title: 'Értesítés beállítva',
        },
        stocktake: {
            type: 'bool',
            title: 'Volt leltár',
        },
        is_template: {
            type: 'bool',
            title: 'Sablon',
        },
        testable: {
            type: 'bool',
            title: 'Testable',
        },
        trackable: {
            type: 'bool',
            title: 'Követésre kötelezett',
        },
        virtual: {
            type: 'bool',
            title: 'Virtuális',
        },
        has_pricing: {
            type: 'bool',
            title: 'Van árazás',
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
            title: 'Aktív'
        },
        is_manufacturer: {
            type: 'bool',
            title: 'Gyártó',
        },
        is_supplier: {
            type: 'bool',
            title: 'Beszállító',
        },
        is_customer: {
            type: 'bool',
            title: 'Vevő',
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
            title: 'Jelölőnégyzet',
        },
        has_choices: {
            type: 'bool',
            title: 'Vannak lehetőségei',
        },
        has_units: {
            type: 'bool',
            title: 'Van mértékegysége',
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
