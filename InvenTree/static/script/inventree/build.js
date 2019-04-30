function makeBuildTable(table, options) {
    /* Construct a table for allocation items to a build.
     * Each row contains a sub_part for the BOM.
     * Each row can be expended to allocate stock items against that part.
     * 
     * options:
     * build - ID of the build object
     * part - ID of the part object for the build
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
                row,
                {
                    build: options.build
                },
            );
        },
        columns: [
            {
                field: 'sub_part_detail.name',
                title: 'Part',
            },
            {
                field: 'quantity',
                title: 'Required',
            },
            {
                field: 'allocated',
                title: 'Allocated',
            }
        ],
    });

    getBomList(
        {
            part: options.part
        }).then(function(response) {
            table.bootstrapTable('load', response)
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

function fillAllocationTable(table, parent_row, options) {
    /* Load data into an allocation table,
     * and update the total stock allocation count in the parent row.
     *
     * table - the part allocation table
     * row - parent row in the build allocation table
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
    });
}