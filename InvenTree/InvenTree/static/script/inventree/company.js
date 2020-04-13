
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

    $(table).inventreeTable({
        url: url,
        method: 'get',
        queryParams: filters,
        groupBy: false,
        formatNoMatches: function() { return "No company information found"; },
        columns: [
            {
                field: 'pk',
                title: 'ID',
                visible: false,
            },
            {
                field: 'name',
                title: 'Company',
                sortable: true,
                formatter: function(value, row, index, field) {
                    var html = imageHoverIcon(row.image) + renderLink(value, row.url);

                    if (row.is_customer) {
                        html += `<span title='Customer' class='fas fa-user-tie label-right'></span>`;
                    }
                    
                    if (row.is_manufacturer) {
                        html += `<span title='Manufacturer' class='fas fa-industry label-right'></span>`;
                    }
                    
                    if (row.is_supplier) {
                        html += `<span title='Supplier' class='fas fa-building label-right'></span>`;
                    }

                    return html;
                }
            },
            {
                field: 'description',
                title: 'Description',
                sortable: true,
            },
            {
                field: 'website',
                title: 'Website',
                formatter: function(value, row, index, field) {
                    if (value) {
                        return renderLink(value, value);
                    }
                    return '';
                }
            },
            {
                field: 'part_count',
                title: 'Parts',
                sortable: true,
                formatter: function(value, row, index, field) {
                    return renderLink(value, row.url + 'parts/');
                }
            },
        ],
    });
}
