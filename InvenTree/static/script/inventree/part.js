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
     *      query: extra query params for API request
     *      buttons: If provided, link buttons to selection status of this table
     */

    // Default query params
    query = options.query;
    
    if (!options.allowInactive) {
        // Only display active parts
        query.active = true;
    }

    $(table).bootstrapTable({
        url: url,
        sortable: true,
        search: true,
        sortName: 'name',
        method: 'get',
        pagination: true,
        pageSize: 25,
        rememberOrder: true,
        formatNoMatches: function() { return "No parts found"; },
        queryParams: function(p) {
            return  query;
        },
        columns: [
            {
                checkbox: true,
                title: 'Select',
                searchable: false,
            },
            {
                field: 'pk',
                title: 'ID',
                visible: false,
            },
            {
                field: 'name',
                title: 'Part',
                sortable: true,
                formatter: function(value, row, index, field) {
                    var name = row.full_name;

                    var display = imageHoverIcon(row.image_url) + renderLink(name, row.url);
                    if (!row.active) {
                        display = display + "<span class='label label-warning' style='float: right;'>INACTIVE</span>";
                    }
                    return display; 
                }
            },
            {
                sortable: true,
                field: 'description',
                title: 'Description',
            },
            {
                sortable: true,
                field: 'category_name',
                title: 'Category',
                formatter: function(value, row, index, field) {
                    if (row.category) {
                        return renderLink(row.category_name, "/part/category/" + row.category + "/");
                    }
                    else {
                        return '';
                    }
                }   
            },
            {
                field: 'total_stock',
                title: 'Stock',
                searchable: false,
                sortable: true,
                formatter: function(value, row, index, field) {
                    if (value) {
                        return renderLink(value, row.url + 'stock/');
                    }
                    else {
                        return "<span class='label label-warning'>No stock</span>";
                    }
                }
            }
        ],
    });

    if (options.buttons) {
        linkButtonsToSelection($(table), options.buttons);
    }
}