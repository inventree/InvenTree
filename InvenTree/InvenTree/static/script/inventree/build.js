function loadBuildTable(table, options) {

    var params = options.params || {};

    var filters = loadTableFilters("build");

    for (var key in params) {
        filters[key] = params[key];
    }

    setupFilterList("build", table);

    table.inventreeTable({
        method: 'get',
        formatNoMatches: function() {
            return "No builds matching query";
        },
        url: options.url,
        queryParams: filters,
        groupBy: false,
        original: params,
        columns: [
            {
                field: 'pk',
                title: 'ID', 
                visible: false,
            },
            {
                field: 'title',
                title: 'Build',
                sortable: true,
                formatter: function(value, row, index, field) {
                    return renderLink(value, '/build/' + row.pk + '/');
                }
            },
            {
                field: 'part',
                title: 'Part',
                sortable: true,
                formatter: function(value, row, index, field) {

                    var name = row.part_detail.full_name;

                    return imageHoverIcon(row.part_detail.thumbnail) + renderLink(name, '/part/' + row.part + '/');
                }
            },
            {
                field: 'quantity',
                title: 'Quantity',
                sortable: true,
            },
            {
                field: 'status',
                title: 'Status',
                sortable: true,
                formatter: function(value, row, index, field) {
                    return buildStatusDisplay(value);
                },
            },
            {
                field: 'creation_date',
                title: 'Created',
                sortable: true,
            },
            {
                field: 'completion_date',
                title: 'Completed',
                sortable: true,
            },
        ],
    });
}


function updateAllocationTotal(id, count, required) {
    
    count = parseFloat(count);
    
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
                    return '' + parseFloat(value.quantity) + ' x ' + value.part_name + ' @ ' + value.location_name;
                }
            },
            {
                field: 'stock_item_detail.quantity',
                title: 'Available',
                formatter: function(value, row, index, field) {
                    return parseFloat(value);
                }
            },
            {
                field: 'quantity',
                title: 'Allocated',
                formatter: function(value, row, index, field) {
                    var html = parseFloat(value);

                    var bEdit = "<button class='btn item-edit-button btn-sm' type='button' title='Edit stock allocation' url='/build/item/" + row.pk + "/edit/'><span class='glyphicon glyphicon-small glyphicon-edit'></span></button>";
                    var bDel = "<button class='btn item-del-button btn-sm' type='button' title='Delete stock allocation' url='/build/item/" + row.pk + "/delete/'><span class='glyphicon glyphicon-small glyphicon-trash'></span></button>";
                    
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
            count += parseFloat(results[i].quantity);
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