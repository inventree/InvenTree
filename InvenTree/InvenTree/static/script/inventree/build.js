function updateAllocationTotal(id, count, required) {
    
    
    $('#allocation-total-'+id).html(count);
    
    var el = $("#allocation-panel-" + id);
    el.removeClass('part-allocation-pass part-allocation-underallocated part-allocation-overallocated');

    if (count < required) {
        el.addClass('part-allocation-underallocated');
    } else if (count > required) {
        el.addClass('part-allocation-overallocated');
    } else {
        el.addClass('part-allocation-pass');
    }
}

function loadAllocationTable(table, part_id, part, url, required, button) {
    
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
                field: 'stock_item_detail.quantity',
                title: 'Available',
            },
            {
                field: 'quantity',
                title: 'Allocated',
                formatter: function(value, row, index, field) {
                    var html = value;

                    var bEdit = "<button class='btn btn-primary item-edit-button btn-sm' type='button' title='Edit stock allocation' url='/build/item/" + row.pk + "/edit/'><span class='glyphicon glyphicon-small glyphicon-edit'></span></button>";
                    var bDel = "<button class='btn btn-danger item-del-button btn-sm' type='button' title='Delete stock allocation' url='/build/item/" + row.pk + "/delete/'><span class='glyphicon glyphicon-small glyphicon-trash'></span></button>";
                    
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
            },
        });
    });

    table.on('load-success.bs.table', function(data) {
        // Extract table data
        var results = table.bootstrapTable('getData');

        var count = 0;

        for (var i = 0; i < results.length; i++) {
            count += results[i].quantity;
        }

        updateAllocationTotal(part_id, count, required);
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

        launchModalForm(button.attr('url'), {
            success: function() {
                table.bootstrapTable('refresh');
            }
        });
    });

}