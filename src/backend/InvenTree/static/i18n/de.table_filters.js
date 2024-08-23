



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
        title: 'Projektcode',
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
        title: 'Hat Projektcode',
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
            title: 'Bestellstatus',
            options: returnOrderCodes
        },
        outstanding: {
            type: 'bool',
            title: 'Ausstehend',
        },
        overdue: {
            type: 'bool',
            title: 'Überfällig',
        },
        assigned_to_me: {
            type: 'bool',
            title: 'Mir zugewiesen',
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
            title: 'Empfangen',
        },
        outcome: {
            title: 'Ergebnis',
            options: returnOrderLineItemCodes,
        }
    };
}


// Return a dictionary of filters for the variants table
function getVariantsTableFilters() {
    return {
        active: {
            type: 'bool',
            title: 'Aktiv',
        },
        template: {
            type: 'bool',
            title: 'Vorlage',
        },
        virtual: {
            type: 'bool',
            title: 'Virtuell',
        },
        testable: {
            type: 'bool',
            title: 'Testable',
        },
        trackable: {
            type: 'bool',
            title: 'Nachverfolgbar',
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
            title: 'Nachverfolgbares Teil',
        },
        sub_part_assembly: {
            type: 'bool',
            title: 'Baugruppe',
        },
        available_stock: {
            type: 'bool',
            title: 'Hat verfügbaren Bestand',
        },
        on_order: {
            type: 'bool',
            title: 'Bestellt',
        },
        validated: {
            type: 'bool',
            title: 'überprüft',
        },
        inherited: {
            type: 'bool',
            title: 'Wird vererbt',
        },
        allow_variants: {
            type: 'bool',
            title: 'Erlaube alternatives Lager',
        },
        optional: {
            type: 'bool',
            title: 'Optional',
        },
        consumable: {
            type: 'bool',
            title: 'Verbrauchsmaterial',
        },
        has_pricing: {
            type: 'bool',
            title: 'Hat Preise',
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
            title: 'Wird vererbt',
        },
        'optional': {
            type: 'bool',
            title: 'Optional',
        },
        'part_active': {
            type: 'bool',
            title: 'Aktiv',
        },
        'part_trackable': {
            type: 'bool',
            title: 'Nachverfolgbar',
        },
    };
}


// Return a dictionary of filters for the "stock location" table
function getStockLocationFilters() {
    return {
        cascade: {
            type: 'bool',
            title: 'Unter-Lagerorte einschließen',
            description: 'Lagerorte einschließen',
        },
        structural: {
            type: 'bool',
            title: 'Strukturell',
        },
        external: {
            type: 'bool',
            title: 'Extern',
        },
        location_type: {
            title: 'Standorttyp',
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
            title: 'Hat Lagerorttyp'
        },
    };
}


// Return a dictionary of filters for the "part category" table
function getPartCategoryFilters() {
    return {
        cascade: {
            type: 'bool',
            title: 'Unterkategorien einschließen',
            description: 'Unterkategorien einschließen',
        },
        structural: {
            type: 'bool',
            title: 'Strukturell',
        },
        starred: {
            type: 'bool',
            title: 'Abonniert',
        },
    };
}


// Return a dictionary of filters for the "customer stock" table
function getCustomerStockFilters() {
    return {
        serialized: {
            type: 'bool',
            title: 'Hat Seriennummer',
        },
        serial_gte: {
            title: 'Seriennummer gt=',
            description: 'Seriennummer größer oder gleich',
        },
        serial_lte: {
            title: 'Seriennummer lt=',
            description: 'Seriennummern kleiner oder gleich',
        },
        serial: {
            title: 'Seriennummer',
            description: 'Seriennummer',
        },
        batch: {
            title: 'Losnummer',
            description: 'Losnummer',
        },
    };
}


// Return a dictionary of filters for the "stock" table
function getStockTableFilters() {
    var filters = {
        active: {
            type: 'bool',
            title: 'Aktive Teile',
            description: 'Bestand aktiver Teile anzeigen',
        },
        assembly: {
            type: 'bool',
            title: 'Baugruppe',
            description: 'Teil ist eine Baugruppe',
        },
        allocated: {
            type: 'bool',
            title: 'Ist zugeordnet',
            description: 'Teil wurde zugeordnet',
        },
        available: {
            type: 'bool',
            title: 'Verfügbar',
            description: 'Lagerartikel ist zur Verwendung verfügbar',
        },
        cascade: {
            type: 'bool',
            title: 'Unter-Lagerorte einschließen',
            description: 'Bestand in Unter-Lagerorten einschließen',
        },
        depleted: {
            type: 'bool',
            title: 'Aufgebraucht',
            description: 'Zeige aufgebrauchte Lagerartikel',
        },
        in_stock: {
            type: 'bool',
            title: 'Auf Lager',
            description: 'Zeige Teile welche im Lager sind',
        },
        is_building: {
            type: 'bool',
            title: 'In Produktion',
            description: 'Zeige Teile welche in Produktion sind',
        },
        include_variants: {
            type: 'bool',
            title: 'Varianten einschließen',
            description: 'Lagerartikel für Teile-Varianten einschließen',
        },
        installed: {
            type: 'bool',
            title: 'Installiert',
            description: 'Zeige Bestand, welcher in einem anderen Teil verbaut ist',
        },
        sent_to_customer: {
            type: 'bool',
            title: 'Zum Kunden geschickt',
            description: 'Zeige Bestand, welcher Kunden zugeordnet ist',
        },
        serialized: {
            type: 'bool',
            title: 'Hat Seriennummer',
        },
        serial: {
            title: 'Seriennummer',
            description: 'Seriennummer',
        },
        serial_gte: {
            title: 'Seriennummer gt=',
            description: 'Seriennummer größer oder gleich',
        },
        serial_lte: {
            title: 'Seriennummer lt=',
            description: 'Seriennummern kleiner oder gleich',
        },
        status: {
            options: stockCodes,
            title: 'Bestandsstatus',
            description: 'Bestandsstatus',
        },
        has_batch: {
            title: 'Hat Batch-Code',
            type: 'bool',
        },
        batch: {
            title: 'Losnummer',
            description: 'Losnummer',
        },
        tracked: {
            title: 'Nachverfolgt',
            description: 'Lagerbestand wird entweder per Batch-Code oder Seriennummer verfolgt',
            type: 'bool',
        },
        has_purchase_price: {
            type: 'bool',
            title: 'Hat Einkaufspreis',
            description: 'Zeige Bestand, für welchen ein Einkaufspreis verfügbar ist',
        },
        expiry_date_lte: {
            type: 'date',
            title: 'Ablaufdatum vor',
        },
        expiry_date_gte: {
            type: 'date',
            title: 'Ablaufdatum nach',
        },
        external: {
            type: 'bool',
            title: 'Externer Standort',
        }
    };

    // Optional filters if stock expiry functionality is enabled
    if (global_settings.STOCK_ENABLE_EXPIRY) {
        filters.expired = {
            type: 'bool',
            title: 'abgelaufen',
            description: 'Zeige abgelaufene Lagerartikel',
        };

        filters.stale = {
            type: 'bool',
            title: 'überfällig',
            description: 'Zeige Bestand, der bald abläuft',
        };
    }

    return filters;
}


// Return a dictionary of filters for the "stock tests" table
function getStockTestTableFilters() {

    return {
        result: {
            type: 'bool',
            title: 'Test bestanden',
        },
        include_installed: {
            type: 'bool',
            title: 'Installierte Teile einschließen',
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
            title: 'Benötigt',
        },
        enabled: {
            type: 'bool',
            title: 'Aktiviert',
        },
    };
}


// Return a dictionary of filters for the "plugins" table
function getPluginTableFilters() {
    return {
        active: {
            type: 'bool',
            title: 'Aktiv',
        },
        builtin: {
            type: 'bool',
            title: 'Integriert',
        },
        sample: {
            type: 'bool',
            title: 'Beispiel',
        },
        installed: {
            type: 'bool',
            title: 'Installiert'
        },
    };
}


// Return a dictionary of filters for the "build" table
function getBuildTableFilters() {

    let filters = {
        status: {
            title: 'Bauauftrags Status',
            options: buildCodes,
        },
        active: {
            type: 'bool',
            title: 'Aktiv',
        },
        overdue: {
            type: 'bool',
            title: 'Überfällig',
        },
        assigned_to_me: {
            type: 'bool',
            title: 'Mir zugewiesen',
        },
        assigned_to: constructOwnerFilter('Verantwortlicher Benutzer'),
        issued_by: constructOwnerFilter('Aufgegeben von'),
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
            title: 'Zugeordnet',
        },
        available: {
            type: 'bool',
            title: 'Verfügbar',
        },
        tracked: {
            type: 'bool',
            title: 'Nachverfolgt',
        },
        consumable: {
            type: 'bool',
            title: 'Verbrauchsmaterial',
        },
        optional: {
            type: 'bool',
            title: 'Optional',
        },
    };
}


// Return a dictionary of filters for the "purchase order line item" table
function getPurchaseOrderLineItemFilters() {
    return {
        pending: {
            type: 'bool',
            title: 'Ausstehend',
        },
        received: {
            type: 'bool',
            title: 'Empfangen',
        },
        order_status: {
            title: 'Bestellstatus',
            options: purchaseOrderCodes,
        },
    };
}


// Return a dictionary of filters for the "purchase order" table
function getPurchaseOrderFilters() {

    var filters = {
        status: {
            title: 'Bestellstatus',
            options: purchaseOrderCodes,
        },
        outstanding: {
            type: 'bool',
            title: 'Ausstehend',
        },
        overdue: {
            type: 'bool',
            title: 'Überfällig',
        },
        assigned_to_me: {
            type: 'bool',
            title: 'Mir zugewiesen',
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
            title: 'Ausstehend',
        }
    };
}


// Return a dictionary of filters for the "sales order" table
function getSalesOrderFilters() {
    var filters = {
        status: {
            title: 'Bestellstatus',
            options: salesOrderCodes,
        },
        outstanding: {
            type: 'bool',
            title: 'Ausstehend',
        },
        overdue: {
            type: 'bool',
            title: 'Überfällig',
        },
        assigned_to_me: {
            type: 'bool',
            title: 'Mir zugewiesen',
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
            title: 'Fertig',
        },
    };
}


// Return a dictionary of filters for the "supplier part" table
function getSupplierPartFilters() {
    return {
        active: {
            type: 'bool',
            title: 'Aktive Teile',
        },
    };
}


// Return a dictionary of filters for the "part" table
function getPartTableFilters() {
    return {
        cascade: {
            type: 'bool',
            title: 'Unterkategorien einschließen',
            description: 'Teile in Unterkategorien einschließen',
        },
        active: {
            type: 'bool',
            title: 'Aktiv',
            description: 'Aktive Teile anzeigen',
        },
        locked: {
            type: 'bool',
            title: 'Locked',
            description: 'Show locked parts',
        },
        assembly: {
            type: 'bool',
            title: 'Baugruppe',
        },
        unallocated_stock: {
            type: 'bool',
            title: 'Verfügbarer Lagerbestand',
        },
        component: {
            type: 'bool',
            title: 'Komponente',
        },
        has_units: {
            type: 'bool',
            title: 'Hat Einheiten',
            description: 'Teil hat definierte Einheiten',
        },
        has_ipn: {
            type: 'bool',
            title: 'Hat IPN',
            description: 'Teil hat Interne Teilenummer',
        },
        has_stock: {
            type: 'bool',
            title: 'Auf Lager',
        },
        low_stock: {
            type: 'bool',
            title: 'Bestand niedrig',
        },
        purchaseable: {
            type: 'bool',
            title: 'Kaufbar',
        },
        salable: {
            type: 'bool',
            title: 'Verkäuflich',
        },
        starred: {
            type: 'bool',
            title: 'Abonniert',
        },
        stocktake: {
            type: 'bool',
            title: 'Hat Inventureinträge',
        },
        is_template: {
            type: 'bool',
            title: 'Vorlage',
        },
        testable: {
            type: 'bool',
            title: 'Testable',
        },
        trackable: {
            type: 'bool',
            title: 'Nachverfolgbar',
        },
        virtual: {
            type: 'bool',
            title: 'Virtuell',
        },
        has_pricing: {
            type: 'bool',
            title: 'Hat Preise',
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
            title: 'Aktiv'
        },
        is_manufacturer: {
            type: 'bool',
            title: 'Hersteller',
        },
        is_supplier: {
            type: 'bool',
            title: 'Zulieferer',
        },
        is_customer: {
            type: 'bool',
            title: 'Kunde',
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
            title: 'Hat Auswahlen',
        },
        has_units: {
            type: 'bool',
            title: 'Hat Einheiten',
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
