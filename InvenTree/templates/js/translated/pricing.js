{% load i18n %}
{% load inventree_extras %}

/* Functions for retrieving and displaying pricing data */

/* globals
    constructForm,
    global_settings,
    imageHoverIcon,
    inventreeGet,
    loadBarChart,
    loadDoughnutChart,
    makeEditButton,
    makeDeleteButton,
    randomColor,
    renderDate,
    renderLink,
    shortenString,
    withTitle,
    wrapButtons,
*/

/* exported
    baseCurrency,
    calculateTotalPrice,
    convertCurrency,
    formatCurrency,
    formatPriceRange,
    loadBomPricingChart,
    loadPartSupplierPricingTable,
    initPriceBreakSet,
    loadPriceBreakTable,
    loadPurchasePriceHistoryTable,
    loadSalesPriceHistoryTable,
    loadVariantPricingChart,
*/


/*
 * Returns the base currency used for conversion operations
 */
function baseCurrency() {
    return global_settings.INVENTREE_DEFAULT_CURRENCY || 'USD';
}



/*
 * format currency (money) value based on current settings
 *
 * Options:
 * - currency: Currency code (uses default value if none provided)
 * - locale: Locale specified (uses default value if none provided)
 * - digits: Maximum number of significant digits (default = 10)
 */
function formatCurrency(value, options={}) {

    if (value == null) {
        return null;
    }

    let maxDigits = options.digits || global_settings.PRICING_DECIMAL_PLACES || 6;
    let minDigits = options.minDigits || global_settings.PRICING_DECIMAL_PLACES_MIN || 0;

    // Extract default currency information
    let currency = options.currency || global_settings.INVENTREE_DEFAULT_CURRENCY || 'USD';

    // Extract locale information
    let locale = options.locale || navigator.language || 'en-US';

    let formatter = new Intl.NumberFormat(
        locale,
        {
            style: 'currency',
            currency: currency,
            maximumFractionDigits: maxDigits,
            minimumFractionDigits: minDigits,
        }
    );

    return formatter.format(value);
}


/*
 * Format a range of prices
 */
function formatPriceRange(price_min, price_max, options={}) {

    var p_min = price_min || price_max;
    var p_max = price_max || price_min;

    var quantity = 1;

    if ('quantity' in options) {
        quantity = options.quantity;
    }

    if (p_min == null && p_max == null) {
        return null;
    }

    p_min = parseFloat(p_min) * quantity;
    p_max = parseFloat(p_max) * quantity;

    var output = '';

    output += formatCurrency(p_min, options);

    if (p_min != p_max) {
        output += ' - ';
        output += formatCurrency(p_max, options);
    }

    return output;
}


// TODO: Implement a better version of caching here
var cached_exchange_rates = null;

/*
 * Retrieve currency conversion rate information from the server
 */
function getCurrencyConversionRates(cache=true) {

    if (cache && cached_exchange_rates != null) {
        return cached_exchange_rates;
    }

    inventreeGet('{% url "api-currency-exchange" %}', {}, {
        async: false,
        success: function(response) {
            cached_exchange_rates = response;
        }
    });

    return cached_exchange_rates;
}


/*
 * Calculate the total price for a given dataset.
 * Within each 'row' in the dataset, the 'price' attribute is denoted by 'key' variable
 *
 * The target currency is determined as follows:
 * 1. Provided as options.currency
 * 2. All rows use the same currency (defaults to this)
 * 3. Use the result of baseCurrency function
 */
function calculateTotalPrice(dataset, value_func, currency_func, options={}) {

    var currency = options.currency;

    var rates = options.rates || getCurrencyConversionRates();

    if (!rates) {
        console.error('Could not retrieve currency conversion information from the server');
        return `<span class='icon-red fas fa-exclamation-circle' title='{% jstrans "Error fetching currency data" %}'></span>`;
    }

    if (!currency) {
        // Try to determine currency from the dataset
        var common_currency = true;

        for (var idx = 0; idx < dataset.length; idx++) {
            let row = dataset[idx];

            var row_currency = currency_func(row);

            if (row_currency == null) {
                continue;
            }

            if (currency == null) {
                currency = row_currency;
            }

            if (currency != row_currency) {
                common_currency = false;
                break;
            }
        }

        // Inconsistent currencies between rows - revert to base currency
        if (!common_currency) {
            currency = baseCurrency();
        }
    }

    var total = null;

    for (var ii = 0; ii < dataset.length; ii++) {
        let row = dataset[ii];

        // Pass the row back to the decoder
        var value = value_func(row);

        // Ignore null values
        if (value == null) {
            continue;
        }

        // Convert to the desired currency
        value = convertCurrency(
            value,
            currency_func(row) || baseCurrency(),
            currency,
            rates
        );

        if (value == null) {
            continue;
        }

        // Total is null until we get a good value
        if (total == null) {
            total = 0;
        }

        total += value;
    }

    // Return raw total instead of formatted value
    if (options.raw) {
        return total;
    }

    return formatCurrency(total, {
        currency: currency,
    });
}


/*
 * Convert from one specified currency into another
 *
 * @param {number} value - numerical value
 * @param {string} source_currency - The source currency code e.g. 'AUD'
 * @param {string} target_currency - The target currency code e.g. 'USD'
 * @param {object} rate_data - Currency exchange rate data received from the server
 */
function convertCurrency(value, source_currency, target_currency, rate_data) {

    if (value == null) {
        console.warn('Null value passed to convertCurrency function');
        return null;
    }

    // Short circuit the case where the currencies are the same
    if (source_currency == target_currency) {
        return value;
    }

    if (rate_data == null) {
        console.error('convertCurrency() called without rate_data');
        return null;
    }

    if (!('base_currency' in rate_data)) {
        console.error('Currency data missing base_currency parameter');
        return null;
    }

    if (!('exchange_rates' in rate_data)) {
        console.error('Currency data missing exchange_rates parameter');
        return null;
    }

    var rates = rate_data['exchange_rates'];

    if (!(source_currency in rates)) {
        console.error(`Source currency '${source_currency}' not found in exchange rate data`);
        return null;
    }

    if (!(target_currency in rates)) {
        console.error(`Target currency '${target_currency}' not found in exchange rate date`);
        return null;
    }

    // We assume that the 'base exchange rate' is 1:1
    return value / rates[source_currency] * rates[target_currency];
}


/*
 * Load BOM pricing chart
 */
function loadBomPricingChart(options={}) {

    var part = options.part;

    if (!part) {
        console.error('No part provided to loadBomPricingChart');
        return;
    }

    var table = options.table || $('#bom-pricing-table');
    var chartElement = options.table || $('#bom-pricing-chart');

    var chart = null;

    options.params = options.params || {};

    options.params.part = part;
    options.params.sub_part_detail = true;
    options.params.ordering = 'name';
    options.params.has_pricing = true;

    table.inventreeTable({
        url: '{% url "api-bom-list" %}',
        name: 'bompricingtable',
        queryParams: options.params,
        original: options.params,
        paginationVAlign: 'bottom',
        pageSize: 10,
        search: false,
        showColumns: false,
        formatNoMatches: function() {
            return '{% jstrans "No BOM data available" %}';
        },
        onLoadSuccess: function(data) {
            // Construct BOM pricing chart
            // Note here that we use stacked bars to denote "min" and "max" costs

            // Ignore any entries without pricing information
            data = data.filter((x) => x.pricing_min != null || x.pricing_max != null);

            // Sort in decreasing order of "maximum price"
            data = data.sort(function(a, b) {
                var pa = parseFloat(a.quantity * (a.pricing_max || a.pricing_min));
                var pb = parseFloat(b.quantity * (b.pricing_max || b.pricing_min));

                return pb - pa;
            });

            var graphLabels = Array.from(data, (x) => x.sub_part_detail.name);
            var minValues = Array.from(data, (x) => x.quantity * (x.pricing_min || x.pricing_max));
            var maxValues = Array.from(data, (x) => x.quantity * (x.pricing_max || x.pricing_min));

            if (chart) {
                chart.destroy();
            }

            // Generate colors
            var colors = Array.from(data, (x) => randomColor());

            chart = loadDoughnutChart(chartElement, {
                labels: graphLabels,
                datasets: [
                    {
                        label: '{% jstrans "Maximum Price" %}',
                        data: maxValues,
                        backgroundColor: colors,
                    },
                    {
                        label: '{% jstrans "Minimum Price" %}',
                        data: minValues,
                        backgroundColor: colors,
                    },
                ]
            });

        },
        columns: [
            {
                field: 'sub_part',
                title: '{% jstrans "Part" %}',
                sortable: true,
                formatter: function(value, row) {
                    var url = `/part/${row.sub_part}/`;

                    var part = row.sub_part_detail;

                    return imageHoverIcon(part.thumbnail) + renderLink(part.full_name, url);
                },
            },
            {
                field: 'quantity',
                title: '{% jstrans "Quantity" %}',
                sortable: true,
            },
            {
                field: 'reference',
                title: '{% jstrans "Reference" %}',
                sortable: true,
            },
            {
                field: 'pricing',
                title: '{% jstrans "Price Range" %}',
                sortable: false,
                formatter: function(value, row) {
                    var min_price = row.pricing_min;
                    var max_price = row.pricing_max;

                    if (min_price == null && max_price == null) {
                        // No pricing information available at all
                        return null;
                    }

                    // If pricing is the same, return single value
                    if (min_price == max_price) {
                        return formatCurrency(min_price * row.quantity);
                    }

                    var output = '';

                    if (min_price != null) {
                        output += formatCurrency(min_price * row.quantity);

                        if (max_price != null) {
                            output += ' - ';
                        }
                    }

                    if (max_price != null) {
                        output += formatCurrency(max_price * row.quantity);
                    }

                    return output;
                }
            }
        ]
    });
}


/*
 * Load a table displaying complete supplier pricing information for a given part
 */
function loadPartSupplierPricingTable(options={}) {

    var part = options.part;

    if (!part) {
        console.error('No part provided to loadPartSupplierPricingTable');
        return;
    }

    var table = options.table || $('#part-supplier-pricing-table');
    var chartElement = options.chart || $('#part-supplier-pricing-chart');

    var chart = null;

    options.params = options.params || {};

    options.params.base_part = part;
    options.params.supplier_detail = true;
    options.params.part_detail = true;

    table.inventreeTable({
        url: '{% url "api-part-supplier-price-list" %}',
        name: 'partsupplierprice',
        queryParams: options.params,
        original: options.params,
        paginationVAlign: 'bottom',
        pageSize: 10,
        pageList: null,
        search: false,
        showColumns: false,
        formatNoMatches: function() {
            return '{% jstrans "No supplier pricing data available" %}';
        },
        onLoadSuccess: function(data) {
            // Update supplier pricing chart

            // Only allow values with pricing information
            data = data.filter((x) => x.price != null);

            // Sort in increasing order of quantity
            data = data.sort((a, b) => (a.quantity - b.quantity));

            var graphLabels = Array.from(data, (x) => (`${x.part_detail.SKU} - {% jstrans "Quantity" %} ${x.quantity}`));
            var graphValues = Array.from(data, (x) => (x.price / x.part_detail.pack_quantity_native));

            if (chart) {
                chart.destroy();
            }

            chart = loadBarChart(chartElement, {
                labels: graphLabels,
                datasets: [
                    {
                        label: '{% jstrans "Supplier Pricing" %}',
                        data: graphValues,
                        backgroundColor: 'rgba(255, 206, 86, 0.2)',
                        borderColor: 'rgb(255, 206, 86)',
                        stepped: true,
                        fill: true,
                    }
                ]
            });
        },
        columns: [
            {
                field: 'supplier',
                title: '{% jstrans "Supplier" %}',
                formatter: function(value, row) {
                    var html = '';

                    html += imageHoverIcon(row.supplier_detail.image);
                    html += renderLink(row.supplier_detail.name, `/company/${row.supplier}/`);

                    return html;
                }
            },
            {
                field: 'sku',
                title: '{% jstrans "SKU" %}',
                sortable: true,
                formatter: function(value, row) {
                    return renderLink(
                        row.part_detail.SKU,
                        `/supplier-part/${row.part}/`
                    );
                }
            },
            {
                sortable: true,
                field: 'quantity',
                title: '{% jstrans "Quantity" %}',
            },
            {
                sortable: true,
                field: 'price',
                title: '{% jstrans "Unit Price" %}',
                formatter: function(value, row) {

                    if (row.price == null) {
                        return '-';
                    }

                    // Convert to unit pricing
                    var unit_price = row.price / row.part_detail.pack_quantity_native;

                    var html = formatCurrency(unit_price, {
                        currency: row.price_currency
                    });

                    if (row.updated != null) {
                        html += `<span class='badge badge-right rounded-pill bg-dark'>${renderDate(row.updated)}</span>`;
                    }


                    return html;
                }
            }
        ]
    });
}


/*
 * Load PriceBreak table.
 */
function loadPriceBreakTable(table, options={}) {

    var name = options.name || 'pricebreak';
    var human_name = options.human_name || 'price break';
    var linkedGraph = options.linkedGraph || null;
    var chart = null;

    table.inventreeTable({
        name: name,
        search: false,
        showColumns: false,
        paginationVAlign: 'bottom',
        pageSize: 10,
        method: 'get',
        formatNoMatches: function() {
            return `{% jstrans "No price break data available" %}`;
        },
        queryParams: {
            part: options.part
        },
        url: options.url,
        onLoadSuccess: function(tableData) {
            if (linkedGraph) {
                // sort array
                tableData = tableData.sort((a, b) => (a.quantity - b.quantity));

                // split up for graph definition
                var graphLabels = Array.from(tableData, (x) => (x.quantity));
                var graphData = Array.from(tableData, (x) => (x.price));

                // Destroy chart if it already exists
                if (chart) {
                    chart.destroy();
                }

                chart = loadBarChart(linkedGraph, {
                    labels: graphLabels,
                    datasets: [
                        {
                            label: '{% jstrans "Unit Price" %}',
                            data: graphData,
                            backgroundColor: 'rgba(255, 206, 86, 0.2)',
                            borderColor: 'rgb(255, 206, 86)',
                            stepped: true,
                            fill: true,
                        },
                    ],
                });
            }
        },
        columns: [
            {
                field: 'pk',
                title: 'ID',
                visible: false,
                switchable: false,
            },
            {
                field: 'quantity',
                title: '{% jstrans "Quantity" %}',
                sortable: true,
            },
            {
                field: 'price',
                title: '{% jstrans "Price" %}',
                sortable: true,
                formatter: function(value, row) {
                    let html = formatCurrency(value, {currency: row.price_currency});

                    let buttons = '';

                    buttons += makeEditButton(`button-${name}-edit`, row.pk, `{% jstrans "Edit" %} ${human_name}`);
                    buttons += makeDeleteButton(`button-${name}-delete`, row.pk, `{% jstrans "Delete" %} ${human_name}"`);

                    html += wrapButtons(buttons);

                    return html;
                }
            },
        ]
    });
}


function initPriceBreakSet(table, options) {

    var part_id = options.part_id;
    var pb_human_name = options.pb_human_name;
    var pb_url_slug = options.pb_url_slug;
    var pb_url = options.pb_url;
    var pb_new_btn = options.pb_new_btn;
    var pb_new_url = options.pb_new_url;

    var linkedGraph = options.linkedGraph || null;

    loadPriceBreakTable(
        table,
        {
            name: pb_url_slug,
            human_name: pb_human_name,
            url: pb_url,
            linkedGraph: linkedGraph,
            part: part_id,
        }
    );

    function reloadPriceBreakTable() {
        table.bootstrapTable('refresh');
    }

    pb_new_btn.click(function() {

        constructForm(pb_new_url, {
            fields: {
                part: {
                    hidden: true,
                    value: part_id,
                },
                quantity: {},
                price: {
                    icon: 'fa-dollar-sign',
                },
                price_currency: {
                    icon: 'fa-coins',
                },
            },
            method: 'POST',
            title: '{% jstrans "Add Price Break" %}',
            onSuccess: reloadPriceBreakTable,
        });
    });

    table.on('click', `.button-${pb_url_slug}-delete`, function() {
        var pk = $(this).attr('pk');

        constructForm(`${pb_url}${pk}/`, {
            method: 'DELETE',
            title: '{% jstrans "Delete Price Break" %}',
            onSuccess: reloadPriceBreakTable,
        });
    });

    table.on('click', `.button-${pb_url_slug}-edit`, function() {
        var pk = $(this).attr('pk');

        constructForm(`${pb_url}${pk}/`, {
            fields: {
                quantity: {},
                price: {
                    icon: 'fa-dollar-sign',
                },
                price_currency: {
                    icon: 'fa-coins',
                },
            },
            title: '{% jstrans "Edit Price Break" %}',
            onSuccess: reloadPriceBreakTable,
        });
    });
}

/*
 * Load purchase price history for the given part
 */
function loadPurchasePriceHistoryTable(options={}) {

    var part = options.part;

    if (!part) {
        console.error('No part provided to loadPurchasePriceHistoryTable');
        return;
    }

    var table = options.table || $('#part-purchase-history-table');
    var chartElement = options.chart || $('#part-purchase-history-chart');

    var chart = null;

    options.params = options.params || {};

    options.params.base_part = part;
    options.params.part_detail = true;
    options.params.order_detail = true;
    options.params.has_pricing = true;

    // Purchase order must be 'COMPLETE'
    options.params.order_status = {{ PurchaseOrderStatus.COMPLETE }};

    table.inventreeTable({
        url: '{% url "api-po-line-list" %}',
        name: 'partpurchasehistory',
        queryParams: options.params,
        original: options.params,
        paginationVAlign: 'bottom',
        pageSize: 10,
        search: false,
        showColumns: false,
        formatNoMatches: function() {
            return '{% jstrans "No purchase history data available" %}';
        },
        onLoadSuccess: function(data) {
            // Update purchase price history chart

            // Only allow values with pricing information
            data = data.filter((x) => x.purchase_price != null);

            // Sort in increasing date order
            data = data.sort((a, b) => (a.order_detail.complete_date - b.order_detail.complete_date));

            var graphLabels = Array.from(data, (x) => (`${x.order_detail.reference} - ${x.order_detail.complete_date}`));
            var graphValues = Array.from(data, (x) => {
                let pp = x.purchase_price;

                let div = 1.0;

                if (x.supplier_part_detail) {
                    div = parseFloat(x.supplier_part_detail.pack_quantity_native);

                    if (isNaN(div) || !isFinite(div)) {
                        div = 1.0;
                    }
                }

                return pp / div;
            });

            if (chart) {
                chart.destroy();
            }

            chart = loadBarChart(chartElement, {
                labels: graphLabels,
                datasets: [
                    {
                        label: '{% jstrans "Purchase Price History" %}',
                        data: graphValues,
                        backgroundColor: 'rgba(255, 206, 86, 0.2)',
                        borderColor: 'rgb(255, 206, 86)',
                        stepped: true,
                        fill: true,
                    }
                ]
            });
        },
        columns: [
            {
                field: 'order',
                title: '{% jstrans "Purchase Order" %}',
                sortable: true,
                formatter: function(value, row) {
                    var order = row.order_detail;

                    if (!order) {
                        return '-';
                    }

                    var html = '';
                    var supplier = row.supplier_part_detail.supplier_detail;

                    html += imageHoverIcon(supplier.thumbnail || supplier.image);
                    html += renderLink(order.reference, `/order/purchase-order/${order.pk}/`);
                    html += ' - ';
                    html += renderLink(supplier.name, `/company/${supplier.pk}/`);

                    return html;
                }
            },
            {
                field: 'order_detail.complete_date',
                title: '{% jstrans "Date" %}',
                sortable: true,
                formatter: function(value) {
                    return renderDate(value);
                }
            },
            {
                field: 'purchase_price',
                title: '{% jstrans "Unit Price" %}',
                sortable: true,
                formatter: function(value, row) {

                    if (row.purchase_price == null) {
                        return '-';
                    }

                    return formatCurrency(
                        row.purchase_price / row.supplier_part_detail.pack_quantity_native,
                        {
                            currency: row.purchase_price_currency
                        }
                    );
                }
            },
        ]
    });
}


/*
 * Load sales price history for the given part
 */
function loadSalesPriceHistoryTable(options={}) {

    var part = options.part;

    if (!part) {
        console.error('No part provided to loadPurchasePriceHistoryTable');
        return;
    }

    var table = options.table || $('#part-sales-history-table');
    var chartElement = options.chart || $('#part-sales-history-chart');

    var chart = null;

    options.params = options.params || {};

    options.params.part = part;
    options.params.order_detail = true;
    options.params.customer_detail = true;

    // Only return results which have pricing information
    options.params.has_pricing = true;

    // Sales order must be 'SHIPPED'
    options.params.order_status = {{ SalesOrderStatus.SHIPPED }};

    table.inventreeTable({
        url: '{% url "api-so-line-list" %}',
        name: 'partsaleshistory',
        queryParams: options.params,
        original: options.params,
        paginationVAlign: 'bottom',
        pageSize: 10,
        search: false,
        showColumns: false,
        formatNoMatches: function() {
            return '{% jstrans "No sales history data available" %}';
        },
        onLoadSuccess: function(data) {
            // Update sales price history chart

            // Ignore any orders which have not shipped
            data = data.filter((x) => x.order_detail.shipment_date != null);

            // Sort in increasing date order
            data = data.sort((a, b) => (a.order_detail.shipment_date - b.order_detail.shipment_date));

            var graphLabels = Array.from(data, (x) => x.order_detail.shipment_date);
            var graphValues = Array.from(data, (x) => x.sale_price);

            if (chart) {
                chart.destroy();
            }

            chart = loadBarChart(chartElement, {
                labels: graphLabels,
                datasets: [
                    {
                        label: '{% jstrans "Sale Price History" %}',
                        data: graphValues,
                        backgroundColor: 'rgba(255, 206, 86, 0.2)',
                        borderColor: 'rgb(255, 206, 86)',
                        stepped: true,
                        fill: true,
                    }
                ]
            });
        },
        columns: [
            {
                field: 'order',
                title: '{% jstrans "Sales Order" %}',
                formatter: function(value, row) {
                    var order = row.order_detail;
                    var customer = row.customer_detail;

                    if (!order) {
                        return '-';
                    }

                    var html = '';

                    html += imageHoverIcon(customer.thumbnail || customer.image);
                    html += renderLink(order.reference, `/order/sales-order/${order.pk}/`);
                    html += ' - ';
                    html += renderLink(customer.name, `/company/${customer.pk}/`);

                    return html;
                }
            },
            {
                field: 'shipment_date',
                title: '{% jstrans "Date" %}',
                formatter: function(value, row) {
                    return renderDate(row.order_detail.shipment_date);
                }
            },
            {
                field: 'sale_price',
                title: '{% jstrans "Sale Price" %}',
                formatter: function(value, row) {
                    return formatCurrency(value, {
                        currency: row.sale_price_currency
                    });
                }
            }
        ]
    });
}


/*
 * Load chart and table for part variant pricing
 */
function loadVariantPricingChart(options={}) {

    var part = options.part;

    if (!part) {
        console.error('No part provided to loadPurchasePriceHistoryTable');
        return;
    }

    var table = options.table || $('#variant-pricing-table');
    var chartElement = options.chart || $('#variant-pricing-chart');

    var chart = null;

    options.params = options.params || {};

    options.params.ancestor = part;

    if (global_settings.PRICING_ACTIVE_VARIANTS) {
        // Filter variants by "active" status
        options.params.active = true;
    }

    table.inventreeTable({
        url: '{% url "api-part-list" %}',
        name: 'variantpricingtable',
        queryParams: options.params,
        original: options.params,
        paginationVAlign: 'bottom',
        pageSize: 10,
        search: false,
        showColumns: false,
        formatNoMatches: function() {
            return '{% jstrans "No variant data available" %}';
        },
        onLoadSuccess: function(data) {
            // Construct variant pricing chart

            data = data.filter((x) => x.pricing_min != null || x.pricing_max != null);

            var graphLabels = Array.from(data, (x) => x.full_name);
            var minValues = Array.from(data, (x) => x.pricing_min || x.pricing_max);
            var maxValues = Array.from(data, (x) => x.pricing_max || x.pricing_min);

            if (chart) {
                chart.destroy();
            }

            chart = loadBarChart(chartElement, {
                labels: graphLabels,
                datasets: [
                    {
                        label: '{% jstrans "Minimum Price" %}',
                        data: minValues,
                        backgroundColor: 'rgba(200, 250, 200, 0.75)',
                        borderColor: 'rgba(200, 250, 200)',
                        stepped: true,
                        fill: true,
                    },
                    {
                        label: '{% jstrans "Maximum Price" %}',
                        data: maxValues,
                        backgroundColor: 'rgba(250, 220, 220, 0.75)',
                        borderColor: 'rgba(250, 220, 220)',
                        stepped: true,
                        fill: true,
                    }
                ]
            });
        },
        columns: [
            {
                field: 'part',
                title: '{% jstrans "Variant Part" %}',
                formatter: function(value, row) {
                    var name = shortenString(row.full_name);
                    var display = imageHoverIcon(row.thumbnail) + renderLink(name, `/part/${row.pk}/`);
                    return withTitle(display, row.full_name);
                }
            },
            {
                field: 'pricing',
                title: '{% jstrans "Price Range" %}',
                formatter: function(value, row) {
                    var min_price = row.pricing_min;
                    var max_price = row.pricing_max;

                    if (min_price == null && max_price == null) {
                        // No pricing information available at all
                        return null;
                    }

                    // If pricing is the same, return single value
                    if (min_price == max_price) {
                        return formatCurrency(min_price);
                    }

                    var output = '';

                    if (min_price != null) {
                        output += formatCurrency(min_price);

                        if (max_price != null) {
                            output += ' - ';
                        }
                    }

                    if (max_price != null) {
                        output += formatCurrency(max_price);
                    }

                    return output;
                }
            }
        ]
    });
}
