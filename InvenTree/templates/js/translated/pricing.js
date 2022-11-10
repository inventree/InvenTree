{% load i18n %}
{% load inventree_extras %}

/* Functions for retrieving and displaying pricing data */

/* globals
*/

/* exported
    loadPartSupplierPricingTable,
    initPriceBreakSet,
    loadPriceBreakTable,
    loadPurchasePriceHistoryTable,
*/


/*
 * Load a table displaying complete supplier pricing information for a given part
 */
function loadPartSupplierPricingTable(options={}) {

    var part = options.part;

    if (!part) {
        console.error("No part provided to loadPurchasePriceHistoryTable");
        return;
    }

    var table = options.table || $('#part-supplier-pricing-table');
    var chartElement = options.chart || $('#part-supplier-pricing-chart');

    var chart = null;

    options.params = options.params || {};

    options.params.base_part = part;
    options.params.supplier_detail = true;
    options.params.supplier_part_detail = true;

    var filters = loadTableFilters('partsupplierpricing');

    for (var key in options.params) {
        filters[key] = options.params[key];
    }

    setupFilterList('partsupplierpricing', table, '#filter-list-partsupplierpricing');

    table.inventreeTable({
        url: '{% url "api-part-supplier-price-list" %}',
        name: 'partsupplierprice',
        queryParams: filters,
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

            // Sort in increasing order of quantity
            data = data.sort((a, b) => (a.quantity - b.quantity));

            var graphLabels = Array.from(data, (x) => (x.quantity));
            var graphValues = Array.from(data, (x) => (x.price));

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
                title: '{% trans "Price" %}',
                formatter: function(value, row) {
                    var html = formatCurrency(row.price, {
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
        console.error("No part provided to loadPurchasePriceHistoryTable");
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

    var filters = loadTableFilters('purchasepricehistory');

    for (var key in options.params) {
        filters[key] = options.params[key];
    }

    setupFilterList('purchasepricehistory', table, '#filter-list-purchasepricehistory');

    table.inventreeTable({
        url: '{% url "api-po-line-list" %}',
        name: 'partpurchasehistory',
        queryParams: filters,
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

            // Sort in increasing date order
            data = data.sort((a, b) => (a.order_detail.complete_date - b.order_detail.complete_date));

            var graphLabels = Array.from(data, (x) => (x.order_detail.complete_date));
            var graphValues = Array.from(data, (x) => (x.purchase_price));

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
                title: '{% trans "Purchase Price" %}',
                sortable: true,
                formatter: function(value, row) {
                    return formatCurrency(value, {
                        currency: row.purchase_price_currency
                    });
                }
            },
        ]
    });
}
