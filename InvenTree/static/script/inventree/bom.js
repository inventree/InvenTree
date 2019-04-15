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
        }
    ];

    if (options.editable) {
        cols.push({
            formatter: function(value, row, index, field) {
                var bEdit = "<button class='btn btn-success bom-edit-button btn-sm' type='button' url='" + row.url + "edit'>Edit</button>";
                var bDelt = "<button class='btn btn-danger bom-delete-button btn-sm' type='button' url='" + row.url + "delete'>Delete</button>";

                return "<div class='btn-group'>" + bEdit + bDelt + "</div>";
            }
        });
    }

    // Part column
    cols.push(
        {
            field: 'sub_part',
            title: 'Part',
            sortable: true,
            formatter: function(value, row, index, field) {
                return renderLink(value.name, value.url);
            }
        }
    );

    // Part description
    cols.push(
        {
            field: 'sub_part.description',
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
        }
    );

    // Part notes
    cols.push(
        {
            field: 'note',
            title: 'Notes',
            searchable: true,
            sortable: false,
        }
    );

    // If we are NOT editing, display the available stock
    if (!options.editable) {
        cols.push(
            {
                field: 'sub_part.available_stock',
                title: 'Available',
                searchable: false,
                sortable: true,
                formatter: function(value, row, index, field) {
                    var text = "";

                    if (row.quantity < row.sub_part.available_stock)
                    {
                        text = "<span class='label label-success'>" + value + "</span>";
                    }
                    else
                    {
                        text = "<span class='label label-warning'>" + value + "</span>";
                    }

                    return renderLink(text, row.sub_part.url + "stock/");
                }
            }
        );
    }

    // Configure the table (bootstrap-table)

    table.bootstrapTable({
        sortable: true,
        search: true,
        clickToSelect: true,
        queryParams: function(p) {
            return {
                part: options.parent_id,
            }
        },
        columns: cols,
        url: options.bom_url
    });

    // In editing mode, attached editables to the appropriate table elements
    if (options.editable) {

        table.on('click', '.bom-delete-button', function() {
            var button = $(this);
            
            launchDeleteForm(button.attr('url'), {
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

        // Callback when the BOM data are successfully loaded
        table.on('load-success.bs.table', function() {
            table.find('.editable-item').editable();
            
            // Table has loaded - Request list of available parts
            // Request list of parts which could (potentially) be added to this BOM
            $.ajax({
                url: options.part_url,
                method: 'GET',
                data: {
                    consumable: true,       // Only list parts that can be used in other parts
                },
                success: function(result, status, xhr) {
                    // Convert returned data to select2 format
                    var data = $.map(result, function(obj) {
                        obj.id = obj.id || obj.pk;        // Part ID is supplied as field 'pk'
                        obj.text = obj.text || obj.name;    // Part text is supplied as field 'name'

                        return obj;
                    });

                    table.find('.part-select').select2({
                        data: data,
                        dropdownAutoWidth: true,
                    }).select2('val', 1);

                    /*
                    // Insert these data into each row drop-down
                    table.find('.editable-part').editable({
                        source: data,
                        select2: {
                            placeholder: 'Select Part',
                            minimumInputLength: 3,
                            dropdownAutoWidth: true,
                        }
                    }).on('shown', function(e, editable){
                        editable.input.$input.select2({
                            //data: data,
                            minimumResultsForSearch: Infinity,
                            dropdownAutoWidth: true,
                            dropdownParent: table,
                        });
                        editable.input.$input.select2('val', editable.input.$input.val());
                      });
                    */
                }
            });
        });

    }

}