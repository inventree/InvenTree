



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
        title: 'Код проекта',
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
            title: 'Статус заказа',
            options: returnOrderCodes
        },
        outstanding: {
            type: 'bool',
            title: 'Невыполненный',
        },
        overdue: {
            type: 'bool',
            title: 'Просрочено',
        },
        assigned_to_me: {
            type: 'bool',
            title: 'Назначено мне',
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
            title: 'Получено',
        },
        outcome: {
            title: 'Результат',
            options: returnOrderLineItemCodes,
        }
    };
}


// Return a dictionary of filters for the variants table
function getVariantsTableFilters() {
    return {
        active: {
            type: 'bool',
            title: 'Активный',
        },
        template: {
            type: 'bool',
            title: 'Шаблон',
        },
        virtual: {
            type: 'bool',
            title: 'Виртуальная',
        },
        testable: {
            type: 'bool',
            title: 'Testable',
        },
        trackable: {
            type: 'bool',
            title: 'Отслеживание',
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
            title: 'Отслеживаемая деталь',
        },
        sub_part_assembly: {
            type: 'bool',
            title: 'Производимая Деталь',
        },
        available_stock: {
            type: 'bool',
            title: 'Has Available Stock',
        },
        on_order: {
            type: 'bool',
            title: 'В заказе',
        },
        validated: {
            type: 'bool',
            title: 'Проверен',
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
            title: 'Необязательно',
        },
        consumable: {
            type: 'bool',
            title: 'Расходники',
        },
        has_pricing: {
            type: 'bool',
            title: 'Имеет цену',
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
            title: 'Необязательно',
        },
        'part_active': {
            type: 'bool',
            title: 'Активный',
        },
        'part_trackable': {
            type: 'bool',
            title: 'Отслеживание',
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
            title: 'Структура',
        },
        external: {
            type: 'bool',
            title: 'Внешний',
        },
        location_type: {
            title: 'Тип Места Хранения',
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
            title: 'Включая подкатегории',
            description: 'Включая подкатегории',
        },
        structural: {
            type: 'bool',
            title: 'Структура',
        },
        starred: {
            type: 'bool',
            title: 'Подписан',
        },
    };
}


// Return a dictionary of filters for the "customer stock" table
function getCustomerStockFilters() {
    return {
        serialized: {
            type: 'bool',
            title: 'Сериализовано',
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
            title: 'Серийный номер',
            description: 'Серийный номер',
        },
        batch: {
            title: 'Партия',
            description: 'Код партии',
        },
    };
}


// Return a dictionary of filters for the "stock" table
function getStockTableFilters() {
    var filters = {
        active: {
            type: 'bool',
            title: 'Активная Деталь',
            description: 'Show stock for active parts',
        },
        assembly: {
            type: 'bool',
            title: 'Производимая деталь',
            description: 'Part is an assembly',
        },
        allocated: {
            type: 'bool',
            title: 'Зарезервировано',
            description: 'Item has been allocated',
        },
        available: {
            type: 'bool',
            title: 'Доступно',
            description: 'Stock is available for use',
        },
        cascade: {
            type: 'bool',
            title: 'Include sublocations',
            description: 'Include stock in sublocations',
        },
        depleted: {
            type: 'bool',
            title: 'Истощен',
            description: 'Показать просроченные складские позиции',
        },
        in_stock: {
            type: 'bool',
            title: 'На складе',
            description: 'Show items which are in stock',
        },
        is_building: {
            type: 'bool',
            title: 'В производстве',
            description: 'Show items which are in production',
        },
        include_variants: {
            type: 'bool',
            title: 'Include Variants',
            description: 'Включить складские позиции для разновидностей деталей',
        },
        installed: {
            type: 'bool',
            title: 'Установлено',
            description: 'Показать складские позиции, установленные в другие детали',
        },
        sent_to_customer: {
            type: 'bool',
            title: 'Отправлено клиенту',
            description: 'Show items which have been assigned to a customer',
        },
        serialized: {
            type: 'bool',
            title: 'Сериализовано',
        },
        serial: {
            title: 'Серийный номер',
            description: 'Серийный номер',
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
            title: 'Статус Запасов',
            description: 'Статус Запасов',
        },
        has_batch: {
            title: 'Имеет код партии',
            type: 'bool',
        },
        batch: {
            title: 'Партия',
            description: 'Код партии',
        },
        tracked: {
            title: 'Отслеживается',
            description: 'Складская позиция отслеживается либо по коду партии, либо серийному номеру',
            type: 'bool',
        },
        has_purchase_price: {
            type: 'bool',
            title: 'Has purchase price',
            description: 'Показать складские позиции, у которых установлена закупочная цена',
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
            title: 'Просрочен',
            description: 'Показать просроченные складские позиции',
        };

        filters.stale = {
            type: 'bool',
            title: 'Залежалый',
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
            title: 'Тест Пройден',
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
            title: 'Требуется',
        },
        enabled: {
            type: 'bool',
            title: 'Включено',
        },
    };
}


// Return a dictionary of filters for the "plugins" table
function getPluginTableFilters() {
    return {
        active: {
            type: 'bool',
            title: 'Активный',
        },
        builtin: {
            type: 'bool',
            title: 'Встроенный',
        },
        sample: {
            type: 'bool',
            title: 'Образец',
        },
        installed: {
            type: 'bool',
            title: 'Установлено'
        },
    };
}


// Return a dictionary of filters for the "build" table
function getBuildTableFilters() {

    let filters = {
        status: {
            title: 'Статус Производства',
            options: buildCodes,
        },
        active: {
            type: 'bool',
            title: 'Активный',
        },
        overdue: {
            type: 'bool',
            title: 'Просрочено',
        },
        assigned_to_me: {
            type: 'bool',
            title: 'Назначено мне',
        },
        assigned_to: constructOwnerFilter('Ответственный'),
        issued_by: constructOwnerFilter('Создано'),
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
            title: 'Зарезервировано',
        },
        available: {
            type: 'bool',
            title: 'Доступно',
        },
        tracked: {
            type: 'bool',
            title: 'Отслеживается',
        },
        consumable: {
            type: 'bool',
            title: 'Расходники',
        },
        optional: {
            type: 'bool',
            title: 'Необязательно',
        },
    };
}


// Return a dictionary of filters for the "purchase order line item" table
function getPurchaseOrderLineItemFilters() {
    return {
        pending: {
            type: 'bool',
            title: 'Ожидаемый',
        },
        received: {
            type: 'bool',
            title: 'Получено',
        },
        order_status: {
            title: 'Статус заказа',
            options: purchaseOrderCodes,
        },
    };
}


// Return a dictionary of filters for the "purchase order" table
function getPurchaseOrderFilters() {

    var filters = {
        status: {
            title: 'Статус заказа',
            options: purchaseOrderCodes,
        },
        outstanding: {
            type: 'bool',
            title: 'Невыполненный',
        },
        overdue: {
            type: 'bool',
            title: 'Просрочено',
        },
        assigned_to_me: {
            type: 'bool',
            title: 'Назначено мне',
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
            title: 'Невыполненный',
        }
    };
}


// Return a dictionary of filters for the "sales order" table
function getSalesOrderFilters() {
    var filters = {
        status: {
            title: 'Статус заказа',
            options: salesOrderCodes,
        },
        outstanding: {
            type: 'bool',
            title: 'Невыполненный',
        },
        overdue: {
            type: 'bool',
            title: 'Просрочено',
        },
        assigned_to_me: {
            type: 'bool',
            title: 'Назначено мне',
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
            title: 'Завершённые',
        },
    };
}


// Return a dictionary of filters for the "supplier part" table
function getSupplierPartFilters() {
    return {
        active: {
            type: 'bool',
            title: 'Активная Деталь',
        },
    };
}


// Return a dictionary of filters for the "part" table
function getPartTableFilters() {
    return {
        cascade: {
            type: 'bool',
            title: 'Включая подкатегории',
            description: 'Включить детали в подкатегориях',
        },
        active: {
            type: 'bool',
            title: 'Активный',
            description: 'Show active parts',
        },
        locked: {
            type: 'bool',
            title: 'Locked',
            description: 'Show locked parts',
        },
        assembly: {
            type: 'bool',
            title: 'Производимая деталь',
        },
        unallocated_stock: {
            type: 'bool',
            title: 'Доступный запас',
        },
        component: {
            type: 'bool',
            title: 'Компонент',
        },
        has_units: {
            type: 'bool',
            title: 'Имеет Ед. Изм.',
            description: 'Part has defined units',
        },
        has_ipn: {
            type: 'bool',
            title: 'Имеет IPN',
            description: 'Part has internal part number',
        },
        has_stock: {
            type: 'bool',
            title: 'В наличии',
        },
        low_stock: {
            type: 'bool',
            title: 'Низкий запас',
        },
        purchaseable: {
            type: 'bool',
            title: 'Можно купить',
        },
        salable: {
            type: 'bool',
            title: 'Можно продавать',
        },
        starred: {
            type: 'bool',
            title: 'Подписан',
        },
        stocktake: {
            type: 'bool',
            title: 'Has stocktake entries',
        },
        is_template: {
            type: 'bool',
            title: 'Шаблон',
        },
        testable: {
            type: 'bool',
            title: 'Testable',
        },
        trackable: {
            type: 'bool',
            title: 'Отслеживание',
        },
        virtual: {
            type: 'bool',
            title: 'Виртуальная',
        },
        has_pricing: {
            type: 'bool',
            title: 'Имеет цену',
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
            title: 'Активный'
        },
        is_manufacturer: {
            type: 'bool',
            title: 'Производитель',
        },
        is_supplier: {
            type: 'bool',
            title: 'Поставщик',
        },
        is_customer: {
            type: 'bool',
            title: 'Покупатель',
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
            title: 'Чекбокс',
        },
        has_choices: {
            type: 'bool',
            title: 'Имеет Варианты',
        },
        has_units: {
            type: 'bool',
            title: 'Имеет Ед. Изм.',
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
