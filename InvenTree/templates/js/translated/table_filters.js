{% load js_i18n %}
{% load status_codes %}
{% load inventree_extras %}

{% include "status_codes.html" with label='stock' options=StockStatus.list %}
{% include "status_codes.html" with label='stockHistory' options=StockHistoryCode.list %}
{% include "status_codes.html" with label='build' options=BuildStatus.list %}
{% include "status_codes.html" with label='purchaseOrder' options=PurchaseOrderStatus.list %}
{% include "status_codes.html" with label='salesOrder' options=SalesOrderStatus.list %}

/* globals
    global_settings
*/

/* exported
    buildStatusDisplay,
    getAvailableTableFilters,
    purchaseOrderStatusDisplay,
    salesOrderStatusDisplay,
    stockHistoryStatusDisplay,
    stockStatusDisplay,
*/


function getAvailableTableFilters(tableKey) {

    tableKey = tableKey.toLowerCase();

    // Filters for "variant" table
    if (tableKey == 'variants') {
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

    // Filters for Bill of Materials table
    if (tableKey == 'bom') {
        return {
            sub_part_trackable: {
                type: 'bool',
                title: '{% trans "Trackable Part" %}',
            },
            sub_part_assembly: {
                type: 'bool',
                title: '{% trans "Assembled Part" %}',
            },
            validated: {
                type: 'bool',
                title: '{% trans "Validated" %}',
            },
            inherited: {
                type: 'bool',
                title: '{% trans "Inherited" %}',
            },
            allow_variants: {
                type: 'bool',
                title: '{% trans "Allow Variant Stock" %}',
            },
        };
    }

    // Filters for the "related parts" table
    if (tableKey == 'related') {
        return {
        };
    }

    // Filters for the "used in" table
    if (tableKey == 'usedin') {
        return {
            'inherited': {
                type: 'bool',
                title: '{% trans "Inherited" %}',
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

    // Filters for "stock location" table
    if (tableKey == 'location') {
        return {
            cascade: {
                type: 'bool',
                title: '{% trans "Include sublocations" %}',
                description: '{% trans "Include locations" %}',
            },
        };
    }

    // Filters for "part category" table
    if (tableKey == 'category') {
        return {
            cascade: {
                type: 'bool',
                title: '{% trans "Include subcategories" %}',
                description: '{% trans "Include subcategories" %}',
            },
            starred: {
                type: 'bool',
                title: '{% trans "Subscribed" %}',
            },
        };
    }

    // Filters for the "customer stock" table (really a subset of "stock")
    if (tableKey == 'customerstock') {
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

    // Filters for the "Stock" table
    if (tableKey == 'stock') {

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

    // Filters for the 'stock test' table
    if (tableKey == 'stocktests') {
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

    // Filters for the 'part test template' table
    if (tableKey == 'parttests') {
        return {
            required: {
                type: 'bool',
                title: '{% trans "Required" %}',
            },
        };
    }

    // Filters for the "Build" table
    if (tableKey == 'build') {
        return {
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
        };
    }

    // Filters for PurchaseOrderLineItem table
    if (tableKey == 'purchaseorderlineitem') {
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

    // Filters for the PurchaseOrder table
    if (tableKey == 'purchaseorder') {

        return {
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
    }

    if (tableKey == 'salesorderallocation') {
        return {
            outstanding: {
                type: 'bool',
                title: '{% trans "Outstanding" %}',
            }
        };
    }

    if (tableKey == 'salesorder') {
        return {
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
        };
    }

    if (tableKey == 'salesorderlineitem') {
        return {
            completed: {
                type: 'bool',
                title: '{% trans "Completed" %}',
            },
        };
    }

    if (tableKey == 'supplier-part') {
        return {
            active: {
                type: 'bool',
                title: '{% trans "Active parts" %}',
            },
        };
    }

    // Filters for "company" table
    if (tableKey == 'company') {
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

    // Filters for the "Parts" table
    if (tableKey == 'parts') {
        return {
            cascade: {
                type: 'bool',
                title: '{% trans "Include subcategories" %}',
                description: '{% trans "Include parts in subcategories" %}',
            },
            has_ipn: {
                type: 'bool',
                title: '{% trans "Has IPN" %}',
                description: '{% trans "Part has internal part number" %}',
            },
            active: {
                type: 'bool',
                title: '{% trans "Active" %}',
                description: '{% trans "Show active parts" %}',
            },
            is_template: {
                type: 'bool',
                title: '{% trans "Template" %}',
            },
            has_stock: {
                type: 'bool',
                title: '{% trans "In stock" %}',
            },
            low_stock: {
                type: 'bool',
                title: '{% trans "Low stock" %}',
            },
            unallocated_stock: {
                type: 'bool',
                title: '{% trans "Available stock" %}',
            },
            assembly: {
                type: 'bool',
                title: '{% trans "Assembly" %}',
            },
            component: {
                type: 'bool',
                title: '{% trans "Component" %}',
            },
            starred: {
                type: 'bool',
                title: '{% trans "Subscribed" %}',
            },
            salable: {
                type: 'bool',
                title: '{% trans "Salable" %}',
            },
            trackable: {
                type: 'bool',
                title: '{% trans "Trackable" %}',
            },
            purchaseable: {
                type: 'bool',
                title: '{% trans "Purchasable" %}',
            },
        };
    }

    // Finally, no matching key
    return {};
}
