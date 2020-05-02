{% load i18n %}

function loadPartTable(table, url, options={}) {
    /* Load part listing data into specified table.
     * 
     * Args:
     *  - table: HTML reference to the table
     *  - url: Base URL for API query
     *  - options: object containing following (optional) fields
     *      checkbox: Show the checkbox column
     *      query: extra query params for API request
     *      buttons: If provided, link buttons to selection status of this table
     *      disableFilters: If true, disable custom filters
     */

    // Ensure category detail is included
    options.params['category_detail'] = true;

    var params = options.params || {};

    var filters = {};
    
    if (!options.disableFilters) {
        filters = loadTableFilters("parts");
    }

    for (var key in params) {
        filters[key] = params[key];
    }

    setupFilterList("parts", $(table));

    var columns = [
        {
            field: 'pk',
            title: 'ID',
            visible: false,
        }
    ];

    if (options.checkbox) {
        columns.push({
            checkbox: true,
            title: '{% trans 'Select' %}',
            searchable: false,
        });
    }

    columns.push({
        field: 'name',
        title: '{% trans 'Part' %}',
        sortable: true,
        formatter: function(value, row, index, field) {

            var name = '';

            if (row.IPN) {
                name += row.IPN;
                name += ' | ';
            }

            name += value;

            if (row.revision) {
                name += ' | ';
                name += row.revision;
            }

            if (row.is_template) {
                name = '<i>' + name + '</i>';
            }

            var display = imageHoverIcon(row.thumbnail) + renderLink(name, '/part/' + row.pk + '/');
            
            if (row.is_template) {
                display += `<span class='fas fa-clone label-right' title='{% trans "Template part" %}'></span>`;
            }
            
            if (row.assembly) {
                display += `<span class='fas fa-tools label-right' title='{% trans "Assembled part" %}'></span>`;
            }

            if (row.starred) {
                display += `<span class='fas fa-star label-right' title='{% trans "Starred part" %}'></span>`;
            }

            if (row.salable) {
                display += `<span class='fas fa-dollar-sign label-right' title='{% trans "Salable part" %}'></span>`;
            }

            /*
            if (row.component) {
                display = display + `<span class='fas fa-cogs label-right' title='Component part'></span>`;
            }
            */
            
            if (!row.active) {
                display += `<span class='label label-warning label-right'>{% trans "Inactive" %}</span>`; 
            }
            return display; 
        }
    });

    columns.push({
        sortable: true,
        field: 'description',
        title: '{% trans 'Description' %}',
        formatter: function(value, row, index, field) {

            if (row.is_template) {
                value = '<i>' + value + '</i>';
            }

            return value;
        }
    });
    
    columns.push({
        sortable: true,
        field: 'category_detail',
        title: '{% trans 'Category' %}',
        formatter: function(value, row, index, field) {
            if (row.category) {
                return renderLink(value.pathstring, "/part/category/" + row.category + "/");
            }
            else {
                return '{% trans "No category" %}';
            }
        }   
    });

    columns.push({
        field: 'in_stock',
        title: '{% trans "Stock" %}',
        searchable: false,
        sortable: true,
        formatter: function(value, row, index, field) {            
            var link = "stock";
            
            if (value) {
                // There IS stock available for this part

                // Is stock "low" (below the 'minimum_stock' quantity)?
                if (row.minimum_stock && row.minimum_stock > value) {
                    value += "<span class='label label-right label-warning'>{% trans "Low stock" %}</span>";
                }

            } else if (row.on_order) {
                // There is no stock available, but stock is on order
                value = "0<span class='label label-right label-primary'>{% trans "On Order" %}: " + row.on_order + "</span>";
                link = "orders";
            } else if (row.building) {
                // There is no stock available, but stock is being built
                value = "0<span class='label label-right label-info'>{% trans "Building" %}: " + row.building + "</span>";
                link = "builds";
            } else {
                // There is no stock available
                value = "0<span class='label label-right label-danger'>{% trans "No Stock" %}</span>";
            }
            
            return renderLink(value, '/part/' + row.pk + "/" + link + "/");
        }
    });

    $(table).inventreeTable({
        url: url,
        sortName: 'name',
        method: 'get',
        queryParams: filters,
        groupBy: false,
        original: params,
        formatNoMatches: function() { return "{% trans "No parts found" %}"; },
        columns: columns,
    });

    if (options.buttons) {
        linkButtonsToSelection($(table), options.buttons);
    }

    /* Button callbacks for part table buttons */

    $("#multi-part-order").click(function() {
        var selections = $(table).bootstrapTable("getSelections");

        var parts = [];

        selections.forEach(function(item) {
            parts.push(item.pk);
        });

        launchModalForm("/order/purchase-order/order-parts/", {
            data: {
                parts: parts,
            },
        });
    });

    $("#multi-part-category").click(function() {
        var selections = $(table).bootstrapTable("getSelections");

        var parts = [];

        selections.forEach(function(item) {
            parts.push(item.pk);
        });

        launchModalForm("/part/set-category/", {
            data: {
                parts: parts,
            },
            reload: true,
        });
    });

    $('#multi-part-export').click(function() {
        var selections = $(table).bootstrapTable("getSelections");

        var parts = '';

        selections.forEach(function(item) {
            parts += item.pk;
            parts += ',';
        });

        location.href = '/part/export/?parts=' + parts;
    });
}