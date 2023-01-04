{% load i18n %}
{% load inventree_extras %}

/* Functions for retrieving and displaying pricing data */

/* globals
*/

/* exported
    loadBomPricingChart,
    loadPartSupplierPricingTable,
    initPriceBreakSet,
    loadPriceBreakTable,
    loadPurchasePriceHistoryTable,
    loadSalesPriceHistoryTable,
    loadVariantPricingChart,
*/


/*
 * Load BOM pricing chart
 */
function loadBomPricingChart(options={}) {

    var part = options.part;

    if (!part) {
        console.error('No part provided to loadPurchasePriceHistoryTable');
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
            return '{% trans "No BOM data available" %}';
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
                        label: '{% trans "Maximum Price" %}',
                        data: maxValues,
                        backgroundColor: colors,
                    },
                    {
                        label: '{% trans "Minimum Price" %}',
                        data: minValues,
                        backgroundColor: colors,
                    },
                ]
            });

        },
        columns: [
            {
                field: 'sub_part',
                title: '{% trans "Part" %}',
                sortable: true,
                formatter: function(value, row) {
                    var url = `/part/${row.sub_part}/`;

                    var part = row.sub_part_detail;

                    return imageHoverIcon(part.thumbnail) + renderLink(part.full_name, url);
                },
            },
            {
                field: 'quantity',
                title: '{% trans "Quantity" %}',
                sortable: true,
            },
            {
                field: 'reference',
                title: '{% trans "Reference" %}',
                sortable: true,
            },
            {
                field: 'pricing',
                title: '{% trans "Price Range" %}',
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
        console.error('No part provided to loadPurchasePriceHistoryTable');
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
            return '{% trans "No supplier pricing data available" %}';
        },
        onLoadSuccess: function(data) {
            // Update supplier pricing chart

            // Only allow values with pricing information
            data = data.filter((x) => x.price != null);

            // Sort in increasing order of quantity
            data = data.sort((a, b) => (a.quantity - b.quantity));

            var graphLabels = Array.from(data, (x) => (`${x.part_detail.SKU} - {% trans "Quantity" %} ${x.quantity}`));
            var graphValues = Array.from(data, (x) => (x.price / x.part_detail.pack_size));

            if (chart) {
                chart.destroy();
            }

            chart = loadBarChart(chartElement, {
                labels: graphLabels,
                datasets: [
                    {
                        label: '{% trans "Supplier Pricing" %}',
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
                title: '{% trans "Supplier" %}',
                formatter: function(value, row) {
                    var html = '';

                    html += imageHoverIcon(row.supplier_detail.image);
                    html += renderLink(row.supplier_detail.name, `/company/${row.supplier}/`);

                    return html;
                }
            },
            {
                field: 'sku',
                title: '{% trans "SKU" %}',
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
                title: '{% trans "Quantity" %}',
            },
            {
                sortable: true,
                field: 'price',
                title: '{% trans "Unit Price" %}',
                formatter: function(value, row) {

                    if (row.price == null) {
                        return '-';
                    }

                    // Convert to unit pricing
                    var unit_price = row.price / row.part_detail.pack_size;

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
            return `{% trans "No price break data available" %}`;
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
                            label: '{% trans "Unit Price" %}',
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
                title: '{% trans "Quantity" %}',
                sortable: true,
            },
            {
                field: 'price',
                title: '{% trans "Price" %}',
                sortable: true,
                formatter: function(value, row) {
                    var html = formatCurrency(value, {currency: row.price_currency});

                    html += `<div class='btn-group float-right' role='group'>`;

                    html += makeIconButton('fa-edit icon-blue', `button-${name}-edit`, row.pk, `{% trans "Edit ${human_name}" %}`);
                    html += makeIconButton('fa-trash-alt icon-red', `button-${name}-delete`, row.pk, `{% trans "Delete ${human_name}" %}`);

                    html += `</div>`;

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
                price: {},
                price_currency: {},
            },
            method: 'POST',
            title: '{% trans "Add Price Break" %}',
            onSuccess: reloadPriceBreakTable,
        });
    });

    table.on('click', `.button-${pb_url_slug}-delete`, function() {
        var pk = $(this).attr('pk');

        constructForm(`${pb_url}${pk}/`, {
            method: 'DELETE',
            title: '{% trans "Delete Price Break" %}',
            onSuccess: reloadPriceBreakTable,
        });
    });

    table.on('click', `.button-${pb_url_slug}-edit`, function() {
        var pk = $(this).attr('pk');

        constructForm(`${pb_url}${pk}/`, {
            fields: {
                quantity: {},
                price: {},
                price_currency: {},
            },
            title: '{% trans "Edit Price Break" %}',
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
            return '{% trans "No purchase history data available" %}';
        },
        onLoadSuccess: function(data) {
            // Update purchase price history chart

            // Only allow values with pricing information
            data = data.filter((x) => x.purchase_price != null);

            // Sort in increasing date order
            data = data.sort((a, b) => (a.order_detail.complete_date - b.order_detail.complete_date));

            var graphLabels = Array.from(data, (x) => (`${x.order_detail.reference} - ${x.order_detail.complete_date}`));
            var graphValues = Array.from(data, (x) => (x.purchase_price / x.supplier_part_detail.pack_size));

            if (chart) {
                chart.destroy();
            }

            chart = loadBarChart(chartElement, {
                labels: graphLabels,
                datasets: [
                    {
                        label: '{% trans "Purchase Price History" %}',
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
                title: '{% trans "Purchase Order" %}',
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
                title: '{% trans "Date" %}',
                sortable: true,
                formatter: function(value) {
                    return renderDate(value);
                }
            },
            {
                field: 'purchase_price',
                title: '{% trans "Unit Price" %}',
                sortable: true,
                formatter: function(value, row) {

                    if (row.purchase_price == null) {
                        return '-';
                    }

                    return formatCurrency(row.purchase_price / row.supplier_part_detail.pack_size, {
                        currency: row.purchase_price_currency
                    });
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
            return '{% trans "No sales history data available" %}';
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
                        label: '{% trans "Sale Price History" %}',
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
                title: '{% trans "Sales Order" %}',
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
                title: '{% trans "Date" %}',
                formatter: function(value, row) {
                    return renderDate(row.order_detail.shipment_date);
                }
            },
            {
                field: 'sale_price',
                title: '{% trans "Sale Price" %}',
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
            return '{% trans "No variant data available" %}';
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
                        label: '{% trans "Minimum Price" %}',
                        data: minValues,
                        backgroundColor: 'rgba(200, 250, 200, 0.75)',
                        borderColor: 'rgba(200, 250, 200)',
                        stepped: true,
                        fill: true,
                    },
                    {
                        label: '{% trans "Maximum Price" %}',
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
                title: '{% trans "Variant Part" %}',
                formatter: function(value, row) {
                    var name = shortenString(row.full_name);
                    var display = imageHoverIcon(row.thumbnail) + renderLink(name, `/part/${row.pk}/`);
                    return withTitle(display, row.full_name);
                }
            },
            {
                field: 'pricing',
                title: '{% trans "Price Range" %}',
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
