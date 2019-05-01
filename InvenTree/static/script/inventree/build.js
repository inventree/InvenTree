function loadAllocationTable(table, part, url, button) {
    
    // Load the allocation table
    table.bootstrapTable({
        url: url,
        sortable: false,
        formatNoMatches: function() { return 'No parts allocated for ' + part; },
        columns: [
            {
                field: 'stock_item_detail',
                title: 'Stock Item',
                formatter: function(value, row, index, field) {
                    return '' + value.quantity + ' x ' + value.part_name + ' @ ' + value.location_name;
                }
            },
            {
                field: 'quantity',
                title: 'Allocated',
                formatter: function(value, row, index, field) {
                    var html = value;

                    var bEdit = "<button class='btn btn-success item-edit-button btn-sm' type='button' url='/build/item/" + row.pk + "/edit/'>Edit</button>";
                    var bDel = "<button class='btn btn-danger item-del-button btn-sm' type='button' url='/build/item/" + row.pk + "/delete/'>Delete</button>";
                    
                    html += "<div class='btn-group' style='float: right;'>" + bEdit + bDel + "</div>";
                    
                    return html;
                }
            }
        ],
    });

    // Callback for 'new-item' button
    button.click(function() {
        launchModalForm(button.attr('url'), {
            success: function() {
                table.bootstrapTable('refresh');
            }
        });
    });

    // Button callbacks for editing and deleting the allocations
    table.on('click', '.item-edit-button', function() {
        var button = $(this);

        launchModalForm(button.attr('url'), {
            success: function() {
                table.bootstrapTable('refresh');
            }
        });
    });

    table.on('click', '.item-del-button', function() {
        var button = $(this);

        launchDeleteForm(button.attr('url'), {
            success: function() {
                table.bootstrapTable('refresh');
            }
        });
    });

}