function makeBuildTable(table, options) {
    /* Construct a table for allocation items to a build.
     * Each row contains a sub_part for the BOM.
     * Each row can be expended to allocate stock items against that part.
     * 
     * options:
     * build - ID of the build object
     * part - ID of the part object for the build
     * new_item_url - URL to create a new BuildItem
     *
     */

    table.bootstrapTable({
        sortable: false,
        detailView: true,
        detailFormatter: function(index, row, element) {
            return makeAllocationTable({
                part: row.pk
            });
        },
        onExpandRow: function(index, row, $detail) {
            fillAllocationTable(
                $("#part-table-" + row.pk),
                index,
                row,
                table,
                {
                    build: options.build
                },
            );
        },
        columns: [
            {
                field: 'pk',
                title: 'ID',
                visible: false,
            },
            {
                field: 'sub_part_detail.name',
                title: 'Part',
            },
            {
                field: 'note',
                title: 'Note',
            },
            {
                field: 'quantity',
                title: 'Required',
            },
            {
                field: 'allocated',
                title: 'Allocated',
                formatter: function(value, row, index, field) {
                    var html = "";

                    var url = options.new_item_url;

                    url += "?build=" + options.build + "&part=" + row.sub_part;
                    
                    if (value) {
                        html = value;
                    } else {
                        html = "0";
                    }

                    html += "<div class='btn-group' style='float: right;'>";

                    html += "<button class='btn btn-success btn-sm new-item-button' type='button' url='" + url + "'>Allocate</button>";

                    html += "</div>";

                    return html;
                }
            },
        ],
    });

    getBomList(
        {
            part: options.part
        }).then(function(response) {
            table.bootstrapTable('load', response)
        });

    // Button callbacks
    table.on('click', '.new-item-button', function() {
        var button = $(this);

        launchModalForm(button.attr('url'), {
            success: function() {
            }
        });
    });
}


function makeAllocationTable(options) {
    /* Construct an allocation table for a single row
     * in the Build table.
     * Each allocation table is a 'detailView' of a parent Part row
     *
     * Options:
     * part: Primary key of the part item
     */

     var table = "<table class='table table-striped table-condensed' ";

     table += "id ='part-table-" + options.part + "' part-id='" + options.part + "'>";
     table += "</table>";

     return table;
}

function fillAllocationTable(table, index, parent_row, parent_table, options) {
    /* Load data into an allocation table,
     * and update the total stock allocation count in the parent row.
     *
     * table - the part allocation table
     * index - row index in the parent table
     * parent_row - parent row data in the build allocation table
     * parent_table - the parent build table
     * 
     * options:
     * build - pk of the Build object
     */

    table.bootstrapTable({
        columns: [
            {
                field: 'stock_item_detail',
                title: 'Stock Item',
                formatter: function(value, row, index, field) {
                    return '' + value.quantity + ' x ' + value.part_name;
                },
            },
            {
                field: 'stock_item_detail.location_name',
                title: 'Location',
            },
            {
                field: 'stock_item_detail.quantity',
                title: 'Available',
                },
            {
                field: 'quantity',
                title: 'Allocated'
            },
        ],
        url: "/api/build/item?build=" + options.build + "&part=" + parent_row.sub_part,
    });

    table.on('load-success.bs.table', function(data) {
        var allocated = 0;

        var allocationData = table.bootstrapTable('getData');
        
        // Calculate total allocation
        for (var i = 0; i < allocationData.length; i++) {
            allocated += allocationData[i].quantity;
        }

        // Update the parent_row data
        parent_row.quantity = allocated;

        /*parent_table.bootstrapTable('updateRow',
            {
                index: index,
                row: parent_row
            }
        );*/
    });
}