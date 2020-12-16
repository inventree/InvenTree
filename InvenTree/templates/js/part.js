{% load i18n %}

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

    var url = '/api/part/star/';

    inventreeGet(
        url,
        {
            part: options.part,
            user: options.user,
        },
        {
            success: function(response) {
                if (response.length == 0) {
                    // Zero length response = star does not exist
                    // So let's add one!
                    inventreePut(
                        url,
                        {
                            part: options.part,
                            user: options.user,
                        },
                        {
                            method: 'POST',
                            success: function(response, status) {
                                $(options.button).addClass('icon-yellow');
                            },
                        }
                    );
                } else {
                    var pk = response[0].pk;
                    // There IS a star (delete it!)
                    inventreePut(
                        url + pk + "/",
                        {
                        },
                        {
                            method: 'DELETE',
                            success: function(response, status) {
                                $(options.button).removeClass('icon-yellow');
                            },
                        }
                    );
                }
            },
        }
    );
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

    setupFilterList("parts", $(table));

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
        sortable: true,
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

    $(table).inventreeTable({
        url: url,
        sortName: 'name',
        method: 'get',
        queryParams: filters,
        groupBy: false,
        name: options.name || 'part',
        original: params,
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
