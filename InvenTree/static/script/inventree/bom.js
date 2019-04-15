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
        // TODO - Add checkbox column
    }

    // Part column
    cols.push(
        {
            field: 'sub_part',
            title: 'Part',
            sortable: true,
            formatter: function(value, row, index, field) {
                if (options.editable) {
                    return renderEditable(value.name,
                        {
                            _pk: row.pk,
                            _type: 'select',
                            _title: 'Part',
                            _class: 'editable-part',
                            _value: 1,
                        });
                }
                else {
                    return renderLink(value.name, value.url);
                }
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
            formatter: function(value, row, index, field) {
                if (options.editable) {
                    return renderEditable(value, 
                        {
                            _pk: row.pk,
                            _title: 'Quantity',
                        });
                }
                else {
                    return value;
                }
            }
        }
    );

    // Part notes
    cols.push(
        {
            field: 'note',
            title: 'Notes',
            searchable: true,
            sortable: false,
            formatter: function(value, row, index, field) {
                if (options.editable) {
                    return renderEditable(value, 
                        {
                            _pk: row.pk,
                            _title: 'Note',
                            _empty: 'Enter note',
                        });
                }
                else {
                    return value; 
                }
            }
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
        queryParams: function(p) {
            return {
                part: options.parent_id,
            }
        },
        columns: cols,
        url: options.bom_url
    });

    if (options.editable) {
        // Callback when the BOM data are successfully loaded
        table.on('load-success.bs.table', function() {
            table.find('.editable-item').editable();
            $("#bom-table").find('.editable-part').editable({
                source: [
                    // Dummy data (for now)
                    {value: 1, text: 'Apple'},
                    {value: 2, text: 'Banana'},
                    {value: 3, text: 'Carrot'},
                ]   
            });
        });
    }

}