/* Part API functions
 * Requires api.js to be loaded first
 */

function getPartCategoryList(filters={}, options={}) {
    return inventreeGet('/api/part/category/', filters, options);
}

function getSupplierPartList(filters={}, options={}) {
    return inventreeGet('/api/part/supplier/', filters, options);
}

function getPartList(filters={}, options={}) {
    return inventreeGet('/api/part/', filters, options);
}

function getBomList(filters={}, options={}) {
    return inventreeGet('/api/bom/', filters, options);
}

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
                                $(options.button).removeClass('glyphicon-star-empty').addClass('glyphicon-star');
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
                                $(options.button).removeClass('glyphicon-star').addClass('glyphicon-star-empty');
                            },
                        }
                    );
                }
            },
        }
    );
}

function loadPartTable(table, url, options={}) {
    /* Load part listing data into specified table.
     * 
     * Args:
     *  - table: HTML reference to the table
     *  - url: Base URL for API query
     *  - options: object containing following (optional) fields
     *      allowInactive: If true, allow display of inactive parts
     *      checkbox: Show the checkbox column
     *      query: extra query params for API request
     *      buttons: If provided, link buttons to selection status of this table
     */

    // Default query params
    query = options.query;
    
    if (!options.allowInactive) {
        // Only display active parts
        query.active = true;
    }

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
            title: 'Select',
            searchable: false,
        });
    }

    columns.push({
        field: 'name',
        title: 'Part',
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

            var display = imageHoverIcon(row.image) + renderLink(name, '/part/' + row.pk + '/');
            
            if (row.is_template) {
                display = display + "<span class='label label-info' style='float: right;'>TEMPLATE</span>";
            }

            if (!row.active) {
                display = display + "<span class='label label-warning' style='float: right;'>INACTIVE</span>";
            }
            return display; 
        }
    });

    columns.push({
        sortable: true,
        field: 'description',
        title: 'Description',
        formatter: function(value, row, index, field) {

            if (row.is_template) {
                value = '<i>' + value + '</i>';
            }

            return value;
        }
    });
    
    columns.push({
        sortable: true,
        field: 'category__name',
        title: 'Category',
        formatter: function(value, row, index, field) {
            if (row.category) {
                return renderLink(row.category__name, "/part/category/" + row.category + "/");
            }
            else {
                return '';
            }
        }   
    });

    columns.push({
        field: 'in_stock',
        title: 'Stock',
        searchable: false,
        sortable: true,
        formatter: function(value, row, index, field) {
            if (value) {
                return renderLink(value, '/part/' + row.pk + '/stock/');
            }
            else {
                return "<span class='label label-warning'>No Stock</span>";
            }
        }
    });

    $(table).inventreeTable({
        url: url,
        sortName: 'name',
        method: 'get',
        formatNoMatches: function() { return "No parts found"; },
        queryParams: function(p) {
            return  query;
        },
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