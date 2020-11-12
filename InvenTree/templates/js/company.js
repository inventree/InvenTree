{% load i18n %}

function loadCompanyTable(table, url, options={}) {
    /*
     * Load company listing data into specified table.
     *
     * Args:
     * - table: Table element on the page
     * - url: Base URL for the API query
     * - options: table options.
     */

    // Query parameters
    var params = options.params || {};

    var filters = loadTableFilters("company");

    for (var key in params) {
        filters[key] = params[key];
    }

    setupFilterList("company", $(table));

    var columns = [
        {
            field: 'pk',
            title: 'ID',
            visible: false,
            switchable: false,
        },
        {
            field: 'name',
            title: '{% trans "Company" %}',
            sortable: true,
            switchable: false,
            formatter: function(value, row, index, field) {
                var html = imageHoverIcon(row.image) + renderLink(value, row.url);

                if (row.is_customer) {
                    html += `<span title='{% trans "Customer" %}' class='fas fa-user-tie label-right'></span>`;
                }
                
                if (row.is_manufacturer) {
                    html += `<span title='{% trans "Manufacturer" %}' class='fas fa-industry label-right'></span>`;
                }
                
                if (row.is_supplier) {
                    html += `<span title='{% trans "Supplier" %}' class='fas fa-building label-right'></span>`;
                }

                return html;
            }
        },
        {
            field: 'description',
            title: '{% trans "Description" %}',
            sortable: true,
        },
        {
            field: 'website',
            title: '{% trans "Website" %}',
            formatter: function(value, row, index, field) {
                if (value) {
                    return renderLink(value, value);
                }
                return '';
            }
        },
    ];

    if (options.pagetype == 'suppliers') {
        columns.push({
            sortable: true,
            field: 'parts_supplied',
            title: '{% trans "Parts Supplied" %}',
            formatter: function(value, row) {
                return renderLink(value, `/company/${row.pk}/parts/`);
            }
        });
    } else if (options.pagetype == 'manufacturers') {
        columns.push({
            sortable: true,
            field: 'parts_manufactured',
            title: '{% trans "Parts Manufactured" %}',
            formatter: function(value, row) {
                return renderLink(value, `/company/${row.pk}/parts/`);
            }
        });
    }

    $(table).inventreeTable({
        url: url,
        method: 'get',
        queryParams: filters,
        groupBy: false,
        formatNoMatches: function() { return "{% trans "No company information found" %}"; },
        showColumns: true,
        name: options.pagetype || 'company',
        columns: columns,
    });
}


function loadSupplierPartTable(table, url, options) {
    /*
     * Load supplier part table
     *
     */

    // Query parameters
    var params = options.params || {};

    // Load filters
    var filters = loadTableFilters("supplier-part");

    for (var key in params) {
        filters[key] = params[key];
    }

    setupFilterList("supplier-part", $(table));

    $(table).inventreeTable({
        url: url,
        method: 'get',
        original: params,
        queryParams: filters,
        name: 'supplierparts',
        groupBy: false,
        formatNoMatches: function() { return "{% trans "No supplier parts found" %}"; },
        columns: [
            {
                checkbox: true,
                switchable: false,
            },
            {
                sortable: true,
                field: 'part_detail.full_name',
                title: '{% trans "Part" %}',
                switchable: false,
                formatter: function(value, row, index, field) {

                    var url = `/part/${row.part}/`;

                    var html = imageHoverIcon(row.part_detail.thumbnail) + renderLink(value, url);

                    if (row.part_detail.is_template) {
                        html += `<span class='fas fa-clone label-right' title='{% trans "Template part" %}'></span>`;
                    }

                    if (row.part_detail.assembly) {
                        html += `<span class='fas fa-tools label-right' title='{% trans "Assembled part" %}'></span>`;
                    }

                    if (!row.part_detail.active) {
                        html += `<span class='label label-warning label-right'>{% trans "Inactive" %}</span>`;
                    }

                    return html;
                }
            },
            {
                sortable: true,
                field: 'supplier',
                title: "{% trans "Supplier" %}",
                formatter: function(value, row, index, field) {
                    if (value) {
                        var name = row.supplier_detail.name;
                        var url = `/company/${value}/`; 
                        var html = imageHoverIcon(row.supplier_detail.image) + renderLink(name, url);

                        return html;
                    } else {
                        return "-";
                    }
                },
            },
            {
                sortable: true,
                field: 'SKU',
                title: "{% trans "Supplier Part" %}",
                formatter: function(value, row, index, field) {
                    return renderLink(value, `/supplier-part/${row.pk}/`);
                }
            },
            {
                sortable: true,
                field: 'manufacturer',
                title: '{% trans "Manufacturer" %}',
                formatter: function(value, row, index, field) {
                    if (value && row.manufacturer_detail) {
                        var name = row.manufacturer_detail.name;
                        var url = `/company/${value}/`;
                        var html = imageHoverIcon(row.manufacturer_detail.image) + renderLink(name, url);

                        return html;
                    } else {
                        return "-";
                    }
                }
            },
            {
                sortable: true,
                field: 'MPN',
                title: '{% trans "MPN" %}',
            },
            {
                field: 'link',
                title: '{% trans "Link" %}',
                formatter: function(value, row, index, field) {
                    if (value) {
                        return renderLink(value, value);
                    } else {
                        return '';
                    }
                }
            },
        ],
    });
}