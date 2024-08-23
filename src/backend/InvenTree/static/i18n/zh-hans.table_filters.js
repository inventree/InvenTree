



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
        title: '專案代碼',
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
        title: '有项目编码',
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
            title: '订单状态',
            options: returnOrderCodes
        },
        outstanding: {
            type: 'bool',
            title: '未完成',
        },
        overdue: {
            type: 'bool',
            title: '逾期',
        },
        assigned_to_me: {
            type: 'bool',
            title: '分配给我',
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
            title: '已接收',
        },
        outcome: {
            title: '结果',
            options: returnOrderLineItemCodes,
        }
    };
}


// Return a dictionary of filters for the variants table
function getVariantsTableFilters() {
    return {
        active: {
            type: 'bool',
            title: '激活',
        },
        template: {
            type: 'bool',
            title: '模板',
        },
        virtual: {
            type: 'bool',
            title: '虚拟的',
        },
        testable: {
            type: 'bool',
            title: 'Testable',
        },
        trackable: {
            type: 'bool',
            title: '可追踪',
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
            title: '可跟踪零件',
        },
        sub_part_assembly: {
            type: 'bool',
            title: '装配零件',
        },
        available_stock: {
            type: 'bool',
            title: '有可用库存',
        },
        on_order: {
            type: 'bool',
            title: '已订购',
        },
        validated: {
            type: 'bool',
            title: '已验证',
        },
        inherited: {
            type: 'bool',
            title: '获取继承的',
        },
        allow_variants: {
            type: 'bool',
            title: '允许变体库存',
        },
        optional: {
            type: 'bool',
            title: '非必須項目',
        },
        consumable: {
            type: 'bool',
            title: '耗材',
        },
        has_pricing: {
            type: 'bool',
            title: '有定价',
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
            title: '获取继承的',
        },
        'optional': {
            type: 'bool',
            title: '非必須項目',
        },
        'part_active': {
            type: 'bool',
            title: '激活',
        },
        'part_trackable': {
            type: 'bool',
            title: '可追踪',
        },
    };
}


// Return a dictionary of filters for the "stock location" table
function getStockLocationFilters() {
    return {
        cascade: {
            type: 'bool',
            title: '包括子位置',
            description: '包括地点',
        },
        structural: {
            type: 'bool',
            title: '结构性',
        },
        external: {
            type: 'bool',
            title: '外部',
        },
        location_type: {
            title: '位置类型',
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
            title: '具有位置类型'
        },
    };
}


// Return a dictionary of filters for the "part category" table
function getPartCategoryFilters() {
    return {
        cascade: {
            type: 'bool',
            title: '包括子类别',
            description: '包括子类别',
        },
        structural: {
            type: 'bool',
            title: '结构性',
        },
        starred: {
            type: 'bool',
            title: '已订阅',
        },
    };
}


// Return a dictionary of filters for the "customer stock" table
function getCustomerStockFilters() {
    return {
        serialized: {
            type: 'bool',
            title: '已序列化',
        },
        serial_gte: {
            title: 'GTE序列号',
            description: '序列号大于或等于',
        },
        serial_lte: {
            title: 'LTE序列号',
            description: '序列号小于或等于',
        },
        serial: {
            title: '序列号',
            description: '序列号',
        },
        batch: {
            title: '队列',
            description: '批号',
        },
    };
}


// Return a dictionary of filters for the "stock" table
function getStockTableFilters() {
    var filters = {
        active: {
            type: 'bool',
            title: '激活的零件',
            description: '显示活动零件的库存',
        },
        assembly: {
            type: 'bool',
            title: '装配',
            description: '零件是一个装配体',
        },
        allocated: {
            type: 'bool',
            title: '已分配',
            description: '项目已分配',
        },
        available: {
            type: 'bool',
            title: '可用數量',
            description: '库存可供使用',
        },
        cascade: {
            type: 'bool',
            title: '包括子位置',
            description: '将库存纳入子位置',
        },
        depleted: {
            type: 'bool',
            title: '已用完',
            description: '显示已耗尽的库存项目',
        },
        in_stock: {
            type: 'bool',
            title: '有库存',
            description: '显示有库存的商品',
        },
        is_building: {
            type: 'bool',
            title: '生产中',
            description: '显示正在生产的项目',
        },
        include_variants: {
            type: 'bool',
            title: '包含变体',
            description: '包括变体零件的库存项',
        },
        installed: {
            type: 'bool',
            title: '已安装',
            description: '显示安装在另一个项目中的库存项目',
        },
        sent_to_customer: {
            type: 'bool',
            title: '寄送給客戶',
            description: '显示已分配给客户的项目',
        },
        serialized: {
            type: 'bool',
            title: '已序列化',
        },
        serial: {
            title: '序列号',
            description: '序列号',
        },
        serial_gte: {
            title: 'GTE序列号',
            description: '序列号大于或等于',
        },
        serial_lte: {
            title: 'LTE序列号',
            description: '序列号小于或等于',
        },
        status: {
            options: stockCodes,
            title: '库存状态',
            description: '库存状态',
        },
        has_batch: {
            title: '有批号',
            type: 'bool',
        },
        batch: {
            title: '队列',
            description: '批号',
        },
        tracked: {
            title: '追蹤中',
            description: '库存项被批号或序列号追踪',
            type: 'bool',
        },
        has_purchase_price: {
            type: 'bool',
            title: '有购买价格',
            description: '显示已设置采购价格的库存项',
        },
        expiry_date_lte: {
            type: 'date',
            title: '过期日期前',
        },
        expiry_date_gte: {
            type: 'date',
            title: '过期日期后',
        },
        external: {
            type: 'bool',
            title: '外部地点',
        }
    };

    // Optional filters if stock expiry functionality is enabled
    if (global_settings.STOCK_ENABLE_EXPIRY) {
        filters.expired = {
            type: 'bool',
            title: '已过期',
            description: '显示已过期的库存商品',
        };

        filters.stale = {
            type: 'bool',
            title: '过期',
            description: '显示即将到期的库存',
        };
    }

    return filters;
}


// Return a dictionary of filters for the "stock tests" table
function getStockTestTableFilters() {

    return {
        result: {
            type: 'bool',
            title: '测试通过',
        },
        include_installed: {
            type: 'bool',
            title: '包括已安装的项目',
        }
    };
}

// Return a dictionary of filters for the "test statistics" table
function getTestStatisticsTableFilters() {

    return {
        finished_datetime_after: {
            type: 'date',
            title: '间隔开始',
        },
        finished_datetime_before: {
            type: 'date',
            title: '间隔结束',
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
            title: '必须的',
        },
        enabled: {
            type: 'bool',
            title: '已启用',
        },
    };
}


// Return a dictionary of filters for the "plugins" table
function getPluginTableFilters() {
    return {
        active: {
            type: 'bool',
            title: '激活',
        },
        builtin: {
            type: 'bool',
            title: '内置',
        },
        sample: {
            type: 'bool',
            title: '样本',
        },
        installed: {
            type: 'bool',
            title: '已安装'
        },
    };
}


// Return a dictionary of filters for the "build" table
function getBuildTableFilters() {

    let filters = {
        status: {
            title: '生产状态',
            options: buildCodes,
        },
        active: {
            type: 'bool',
            title: '激活',
        },
        overdue: {
            type: 'bool',
            title: '逾期',
        },
        assigned_to_me: {
            type: 'bool',
            title: '分配给我',
        },
        assigned_to: constructOwnerFilter('負責人'),
        issued_by: constructOwnerFilter('发布者'),
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
            title: '已分配',
        },
        available: {
            type: 'bool',
            title: '可用數量',
        },
        tracked: {
            type: 'bool',
            title: '追蹤中',
        },
        consumable: {
            type: 'bool',
            title: '耗材',
        },
        optional: {
            type: 'bool',
            title: '非必須項目',
        },
    };
}


// Return a dictionary of filters for the "purchase order line item" table
function getPurchaseOrderLineItemFilters() {
    return {
        pending: {
            type: 'bool',
            title: '待定',
        },
        received: {
            type: 'bool',
            title: '已接收',
        },
        order_status: {
            title: '订单状态',
            options: purchaseOrderCodes,
        },
    };
}


// Return a dictionary of filters for the "purchase order" table
function getPurchaseOrderFilters() {

    var filters = {
        status: {
            title: '订单状态',
            options: purchaseOrderCodes,
        },
        outstanding: {
            type: 'bool',
            title: '未完成',
        },
        overdue: {
            type: 'bool',
            title: '逾期',
        },
        assigned_to_me: {
            type: 'bool',
            title: '分配给我',
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
            title: '未完成',
        }
    };
}


// Return a dictionary of filters for the "sales order" table
function getSalesOrderFilters() {
    var filters = {
        status: {
            title: '订单状态',
            options: salesOrderCodes,
        },
        outstanding: {
            type: 'bool',
            title: '未完成',
        },
        overdue: {
            type: 'bool',
            title: '逾期',
        },
        assigned_to_me: {
            type: 'bool',
            title: '分配给我',
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
            title: '已完成',
        },
    };
}


// Return a dictionary of filters for the "supplier part" table
function getSupplierPartFilters() {
    return {
        active: {
            type: 'bool',
            title: '激活的零件',
        },
    };
}


// Return a dictionary of filters for the "part" table
function getPartTableFilters() {
    return {
        cascade: {
            type: 'bool',
            title: '包括子类别',
            description: '在子类别中包含零件',
        },
        active: {
            type: 'bool',
            title: '激活',
            description: '显示活动零件',
        },
        locked: {
            type: 'bool',
            title: '已锁定',
            description: '显示锁定的零件',
        },
        assembly: {
            type: 'bool',
            title: '装配',
        },
        unallocated_stock: {
            type: 'bool',
            title: '可用库存',
        },
        component: {
            type: 'bool',
            title: '组件',
        },
        has_units: {
            type: 'bool',
            title: '有单位',
            description: '零件已定义单位',
        },
        has_ipn: {
            type: 'bool',
            title: '有内部零件号',
            description: '零件有内部零件号',
        },
        has_stock: {
            type: 'bool',
            title: '有库存',
        },
        low_stock: {
            type: 'bool',
            title: '低库存',
        },
        purchaseable: {
            type: 'bool',
            title: '可购买的',
        },
        salable: {
            type: 'bool',
            title: '可销售',
        },
        starred: {
            type: 'bool',
            title: '已订阅',
        },
        stocktake: {
            type: 'bool',
            title: '有盘点记录',
        },
        is_template: {
            type: 'bool',
            title: '模板',
        },
        testable: {
            type: 'bool',
            title: 'Testable',
        },
        trackable: {
            type: 'bool',
            title: '可追踪',
        },
        virtual: {
            type: 'bool',
            title: '虚拟的',
        },
        has_pricing: {
            type: 'bool',
            title: '有定价',
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
            title: '激活'
        },
        is_manufacturer: {
            type: 'bool',
            title: '制造商',
        },
        is_supplier: {
            type: 'bool',
            title: '供应商',
        },
        is_customer: {
            type: 'bool',
            title: '客户',
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
            title: '勾选框',
        },
        has_choices: {
            type: 'bool',
            title: '有选项',
        },
        has_units: {
            type: 'bool',
            title: '有单位',
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
