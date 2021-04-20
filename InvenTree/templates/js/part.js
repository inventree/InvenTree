{% load i18n %}
{% load inventree_extras %}

/* Part API functions
 * Requires api.js to be loaded first
 */

function toggleStar(options) {
    /* Toggle the 'starred' status of a part.
     * Performs AJAX queries and updates the display on the button.
     * 
     * options:
     * - button: ID of the button (default = '#part-star-icon')
     * - part: pk of the part object
     * - user: pk of the user
     */

    var url = `/api/part/${options.part}/`;

    inventreeGet(url, {}, {
        success: function(response) {
            var starred = response.starred;

            inventreePut(
                url,
                {
                    starred: !starred,
                },
                {
                    method: 'PATCH',
                    success: function(response) {
                        if (response.starred) {
                            $(options.button).addClass('icon-yellow');
                        } else {
                            $(options.button).removeClass('icon-yellow');
                        }
                    }
                }
            );
        }
    });
}


function makePartIcons(part, options={}) {
    /* Render a set of icons for the given part.
     */

    var html = '';

    if (part.trackable) {
        html += makeIconBadge('fa-directions', '{% trans "Trackable part" %}');
    }

    if (part.virtual) {
        html += makeIconBadge('fa-ghost', '{% trans "Virtual part" %}');
    }

    if (part.is_template) {
        html += makeIconBadge('fa-clone', '{% trans "Template part" %}');
    }
    
    if (part.assembly) {
        html += makeIconBadge('fa-tools', '{% trans "Assembled part" %}');
    }

    if (part.starred) {
        html += makeIconBadge('fa-star', '{% trans "Starred part" %}');
    }

    if (part.salable) {
        html += makeIconBadge('fa-dollar-sign', title='{% trans "Salable part" %}');
    }
    
    if (!part.active) {
        html += `<span class='label label-warning label-right'>{% trans "Inactive" %}</span>`; 
    }

    return html;
    
}


function loadPartVariantTable(table, partId, options={}) {
    /* Load part variant table
     */

    var params = options.params || {};

    params.ancestor = partId;

    // Load filters
    var filters = loadTableFilters("variants");

    for (var key in params) {
        filters[key] = params[key];
    }

    setupFilterList("variants", $(table));

    var cols = [
        {
            field: 'pk',
            title: 'ID',
            visible: false,
            switchable: false,
        },
        {
            field: 'name',
            title: '{% trans "Name" %}',
            switchable: false,
            formatter: function(value, row, index, field) {
                var html = '';

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

                html += imageHoverIcon(row.thumbnail);
                html += renderLink(name, `/part/${row.pk}/`);

                if (row.trackable) {
                    html += makeIconBadge('fa-directions', '{% trans "Trackable part" %}');
                }

                if (row.virtual) {
                    html += makeIconBadge('fa-ghost', '{% trans "Virtual part" %}');
                }

                if (row.is_template) {
                    html += makeIconBadge('fa-clone', '{% trans "Template part" %}');
                }
                
                if (row.assembly) {
                    html += makeIconBadge('fa-tools', '{% trans "Assembled part" %}');
                }

                if (!row.active) {
                    html += `<span class='label label-warning label-right'>{% trans "Inactive" %}</span>`; 
                }

                return html;
            },
        },
        {
            field: 'IPN',
            title: '{% trans "IPN" %}',
        },
        {
            field: 'revision',
            title: '{% trans "Revision" %}',
        },
        {
            field: 'description',
            title: '{% trans "Description" %}',
        },
        {
            field: 'in_stock',
            title: '{% trans "Stock" %}',
            formatter: function(value, row) {
                return renderLink(value, `/part/${row.pk}/stock/`);
            }
        }
    ];

    table.inventreeTable({
        url: "{% url 'api-part-list' %}",
        name: 'partvariants',
        showColumns: true,
        original: params,
        queryParams: filters,
        formatNoMatches: function() { return '{% trans "No variants found" %}'; },
        columns: cols,
        treeEnable: true,
        rootParentId: partId,
        parentIdField: 'variant_of',
        idField: 'pk',
        uniqueId: 'pk',
        treeShowField: 'name',
        sortable: true,
        search: true,
        onPostBody: function() {
            table.treegrid({
                treeColumn: 0,
            });

            table.treegrid('collapseAll');
        }
    });
}


function loadSimplePartTable(table, url, options={}) {

    options.disableFilters = true;

    loadPartTable(table, url, options);
}


function loadParametricPartTable(table, options={}) {
    /* Load parametric table for part parameters
     * 
     * Args:
     *  - table: HTML reference to the table
     *  - table_headers: Unique parameters found in category
     *  - table_data: Parameters data
     */

    var table_headers = options.headers
    var table_data = options.data

    var columns = [];

    for (header of table_headers) {
        if (header === 'part') {
            columns.push({
                field: header,
                title: '{% trans "Part" %}',
                sortable: true,
                sortName: 'name',
                formatter: function(value, row, index, field) {

                    var name = '';

                    if (row.IPN) {
                        name += row.IPN + ' | ' + row.name;
                    } else {
                        name += row.name;
                    }
                    
                    return renderLink(name, '/part/' + row.pk + '/'); 
                }
            });
        } else if (header === 'description') {
            columns.push({
                field: header,
                title: '{% trans "Description" %}',
                sortable: true,
            });
        } else {
            columns.push({
                field: header,
                title: header,
                sortable: true,
                filterControl: 'input',
                /* TODO: Search icons are not displayed */
                /*clear: 'fa-times icon-red',*/
            });
        }
    }

    $(table).inventreeTable({
        sortName: 'part',
        queryParams: table_headers,
        groupBy: false,
        name: options.name || 'parametric',
        formatNoMatches: function() { return '{% trans "No parts found" %}'; },
        columns: columns,
        showColumns: true,
        data: table_data,
        filterControl: true,
    });
}


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

    setupFilterList("parts", $(table), options.filterTarget || null);

    var columns = [
        {
            field: 'pk',
            title: 'ID',
            visible: false,
            switchable: false,
            searchable: false,
        }
    ];

    if (options.checkbox) {
        columns.push({
            checkbox: true,
            title: '{% trans "Select" %}',
            searchable: false,
            switchable: false,
        });
    }

    columns.push({
        field: 'IPN',
        title: 'IPN',
        sortable: true,
    }),

    columns.push({
        field: 'name',
        title: '{% trans "Part" %}',
        sortable: true,
        switchable: false,
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
            
            display += makePartIcons(row);

            return display; 
        }
    });

    columns.push({
        field: 'description',
        title: '{% trans "Description" %}',
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
        title: '{% trans "Category" %}',
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

    columns.push({
        field: 'link',
        title: '{% trans "Link" %}',
        formatter: function(value, row, index, field) {
            return renderLink(
                value, value,
                {
                    max_length: 32,
                    remove_http: true,
                }
            );
        }
    });

    $(table).inventreeTable({
        url: url,
        method: 'get',
        queryParams: filters,
        groupBy: false,
        name: options.name || 'part',
        original: params,
        sidePagination: 'server',
        pagination: 'true',
        formatNoMatches: function() { return '{% trans "No parts found" %}'; },
        columns: columns,
        showColumns: true,
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


function loadPartCategoryTable(table, options) {
    /* Display a table of part categories */

    var params = options.params || {};

    var filterListElement = options.filterList || '#filter-list-category';

    var filters = {};

    var filterKey = options.filterKey || options.name || 'category';

    if (!options.disableFilters) {
        filters = loadTableFilters(filterKey);
    }

    var original = {};

    for (var key in params) {
        original[key] = params[key];
        filters[key] = params[key];
    }

    setupFilterList(filterKey, table, filterListElement);

    table.inventreeTable({
        method: 'get',
        url: options.url || '{% url "api-part-category-list" %}',
        queryParams: filters,
        sidePagination: 'server',
        name: 'category',
        original: original,
        showColumns: true,
        columns: [
            {
                checkbox: true,
                title: '{% trans "Select" %}',
                searchable: false,
                switchable: false,
                visible: false,
            },
            {
                field: 'name',
                title: '{% trans "Name" %}',
                switchable: true,
                sortable: true,
                formatter: function(value, row) {
                    return renderLink(
                        value,
                        `/part/category/${row.pk}/`
                    );
                }
            },
            {
                field: 'description',
                title: '{% trans "Description" %}',
                switchable: true,
                sortable: false,
            },
            {
                field: 'pathstring',
                title: '{% trans "Path" %}',
                switchable: true,
                sortable: false,
            },
            {
                field: 'parts',
                title: '{% trans "Parts" %}',
                switchable: true,
                sortable: false,
            }
        ]
    });
}


function yesNoLabel(value) {
    if (value) {
        return `<span class='label label-green'>{% trans "YES" %}</span>`;
    } else {
        return `<span class='label label-yellow'>{% trans "NO" %}</span>`;
    }
}


function loadPartTestTemplateTable(table, options) {
    /*
     * Load PartTestTemplate table.
     */
    
    var params = options.params || {};

    var part = options.part || null;

    var filterListElement = options.filterList || '#filter-list-parttests';

    var filters = loadTableFilters("parttests");

    var original = {};

    for (var key in params) {
        original[key] = params[key];
    }

    setupFilterList("parttests", table, filterListElement);

    // Override the default values, or add new ones
    for (var key in params) {
        filters[key] = params[key];
    }

    table.inventreeTable({
        method: 'get',
        formatNoMatches: function() {
            return '{% trans "No test templates matching query" %}';
        },
        url: "{% url 'api-part-test-template-list' %}",
        queryParams: filters,
        name: 'testtemplate',
        original: original,
        columns: [
            {
                field: 'pk',
                title: 'ID',
                visible: false,
            },
            {
                field: 'test_name',
                title: '{% trans "Test Name" %}',
                sortable: true,
            },
            {
                field: 'description',
                title: '{% trans "Description" %}',
            },
            {
                field: 'required',
                title: "{% trans 'Required' %}",
                sortable: true,
                formatter: function(value) {
                    return yesNoLabel(value);
                }
            },
            {
                field: 'requires_value',
                title: '{% trans "Requires Value" %}',
                formatter: function(value) {
                    return yesNoLabel(value);
                }
            },
            {
                field: 'requires_attachment',
                title: '{% trans "Requires Attachment" %}',
                formatter: function(value) {
                    return yesNoLabel(value);
                }
            },
            {
                field: 'buttons',
                formatter: function(value, row) {
                    var pk = row.pk;

                    if (row.part == part) {
                        var html = `<div class='btn-group float-right' role='group'>`;
                        
                        html += makeIconButton('fa-edit icon-blue', 'button-test-edit', pk, '{% trans "Edit test result" %}');
                        html += makeIconButton('fa-trash-alt icon-red', 'button-test-delete', pk, '{% trans "Delete test result" %}');

                        html += `</div>`;

                        return html;
                    } else {
                        var text = '{% trans "This test is defined for a parent part" %}';

                        return renderLink(text, `/part/${row.part}/tests/`); 
                    }
                }
            }
        ]
    });
}
