/* BOM management functions.
 * Requires follwing files to be loaded first:
 * - api.js
 * - part.js
 * - modals.js
 */


function reloadBomTable(table, options) {

    table.bootstrapTable('refresh');
}


function loadBomTable(table, options) {
    /* Load a BOM table with some configurable options.
     * 
     * Following options are available:
     * editable      - Should the BOM table be editable?
     * bom_url       - Address to request BOM data from
     * part_url      - Address to request Part data from
     * parent_id     - Parent ID of the owning part
     * 
     * BOM data are retrieved from the server via AJAX query
     */

    // Construct the table columns

    var cols = [
        {
            field: 'pk',
            title: 'ID',
            visible: false,
        },
    ];

    if (options.editable) {
        cols.push({
            checkbox: true,
            title: 'Select',
            searchable: false,
            sortable: false,
        });
    }

    // Part column
    cols.push(
        {
            field: 'sub_part_detail.full_name',
            title: 'Part',
            sortable: true,
            formatter: function(value, row, index, field) {
                return imageHoverIcon(row.sub_part_detail.image_url) + renderLink(row.sub_part_detail.full_name, row.sub_part_detail.url);
            }
        }
    );

    // Part description
    cols.push(
        {
            field: 'sub_part_detail.description',
            title: 'Description',
        }
    );

    // Part quantity
    cols.push(
        {
            field: 'quantity',
            title: 'Required',
            searchable: false,
            sortable: true,
            formatter: function(value, row, index, field) {
                var text = value;

                if (row.overage) {
                    text += "<small> (+" + row.overage + ")    </small>";
                }

                return text;
            },
            footerFormatter: function(data) {
                var quantity = 0;

                data.forEach(function(item) {
                    quantity += item.quantity;
                });

                return quantity;
            },
        }
    );

    if (!options.editable) {
        cols.push(
        {
            field: 'sub_part_detail.total_stock',
            title: 'Available',
            searchable: false,
            sortable: true,
            formatter: function(value, row, index, field) {
                var text = "";
                
                if (row.quantity < row.sub_part_detail.total_stock)
                {
                    text = "<span class='label label-success'>" + value + "</span>";
                }
                else
                {
                    if (!value) {
                        value = 'No Stock';
                    }
                    text = "<span class='label label-warning'>" + value + "</span>";
                }
                
                return renderLink(text, row.sub_part_detail.url + "stock/");
            }
        });

        cols.push(
        {
            field: 'price_range',
            title: 'Price',
            sortable: true,
            formatter: function(value, row, index, field) {
                if (value) {
                    return value;
                } else {
                    return "<span class='warning-msg'>No pricing available</span>";
                }
            }
        });

    }
    
    // Part notes
    cols.push(
        {
            field: 'note',
            title: 'Notes',
            searchable: true,
            sortable: true,
        }
    );

    if (options.editable) {
        cols.push({
            formatter: function(value, row, index, field) {
                var bEdit = "<button title='Edit BOM Item' class='btn btn-primary bom-edit-button btn-sm' type='button' url='/part/bom/" + row.pk + "/edit'><span class='glyphicon glyphicon-small glyphicon-edit'></span></button>";
                var bDelt = "<button title='Delete BOM Item' class='btn btn-danger bom-delete-button btn-sm' type='button' url='/part/bom/" + row.pk + "/delete'><span class='glyphicon glyphicon-small glyphicon-trash'></span></button>";
                
                return "<div class='btn-group' role='group'>" + bEdit + bDelt + "</div>";
            }
        });
    }

    // Configure the table (bootstrap-table)

    var params = {
        part: options.parent_id,
        ordering: 'name',
    }

    if (options.part_detail) {
        params.part_detail = true;
    }

    if (options.sub_part_detail) {
        params.sub_part_detail = true;
    }
    
    table.bootstrapTable({
        sortable: true,
        search: true,
        formatNoMatches: function() { return "No BOM items found"; },
        clickToSelect: true,
        showFooter: true,
        queryParams: function(p) {
            return params;
        },
        columns: cols,
        url: options.bom_url
    });

    // In editing mode, attached editables to the appropriate table elements
    if (options.editable) {

        table.on('click', '.bom-delete-button', function() {
            var button = $(this);
            
            launchModalForm(button.attr('url'), {
                                success: function() {
                                    reloadBomTable(table);
                                }
            });
        });

        table.on('click', '.bom-edit-button', function() {
            var button = $(this);

            launchModalForm(button.attr('url'), {
                                success: function() {
                                    reloadBomTable(table);
                                }
            });
        });
    }
}