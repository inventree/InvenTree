{% load i18n %}
{% load inventree_extras %}

function newBuildOrder(options={}) {
    /* Launch modal form to create a new BuildOrder.
     */

    launchModalForm(
        "{% url 'build-create' %}",
        {
            follow: true,
            data: options.data || {},
            callback: [
                {
                    field: 'part',
                    action: function(value) {
                        inventreeGet(
                            `/api/part/${value}/`, {},
                            {
                                success: function(response) {

                                    //enableField('serial_numbers', response.trackable);
                                    //clearField('serial_numbers');
                                }
                            }
                        );
                    },
                }
            ],
        }
    )
}


function makeBuildOutputActionButtons(output, buildInfo) {
    /* Generate action buttons for a build output.
     */

    var buildId = buildInfo.pk;
    var outputId = output.pk;

    var panel = `#allocation-panel-${outputId}`;

    function reloadTable() {
        $(panel).find(`#allocation-table-${outputId}`).bootstrapTable('refresh');
    }
    
    // Find the div where the buttons will be displayed
    var buildActions = $(panel).find(`#output-actions-${outputId}`);

    var html = `<div class='btn-group float-right' role='group'>`;

    // Add a button to "auto allocate" against the build
    html += makeIconButton(
        'fa-magic icon-blue', 'button-output-auto', outputId,
        '{% trans "Auto-allocate stock items to this output" %}',
    );

    // Add a button to "complete" the particular build output
    html += makeIconButton(
        'fa-check icon-green', 'button-output-complete', outputId,
        '{% trans "Complete build output" %}',
        {
            //disabled: true
        }
    );

    // Add a button to "cancel" the particular build output (unallocate)
    html += makeIconButton(
        'fa-minus-circle icon-red', 'button-output-unallocate', outputId,
        '{% trans "Unallocate stock from build output" %}',
    );

    // Add a button to "delete" the particular build output
    html += makeIconButton(
        'fa-trash-alt icon-red', 'button-output-delete', outputId,
        '{% trans "Delete build output" %}',
    );

    // Add a button to "destroy" the particular build output (mark as damaged, scrap)
    // TODO

    html += '</div>';

    buildActions.html(html);

    // Add callbacks for the buttons
    $(panel).find(`#button-output-auto-${outputId}`).click(function() {
        // Launch modal dialog to perform auto-allocation
        launchModalForm(`/build/${buildId}/auto-allocate/`,
            {
                data: {
                    output: outputId,
                },
                success: reloadTable,
            }
        );
    });

    $(panel).find(`#button-output-complete-${outputId}`).click(function() {
        launchModalForm(
            `/build/${buildId}/complete-output/`,
            {
                data: {
                    output: outputId,
                },
                reload: true,
            }
        );  
    });

    $(panel).find(`#button-output-unallocate-${outputId}`).click(function() {
        launchModalForm(
            `/build/${buildId}/unallocate/`,
            {
                success: reloadTable,
                data: {
                    output: outputId,
                }
            }
        );
    });

    $(panel).find(`#button-output-delete-${outputId}`).click(function() {
        launchModalForm(
            `/build/${buildId}/delete-output/`,
            {
                reload: true,
                data: {
                    output: outputId
                }
            }
        );
    });
}


function loadBuildOutputAllocationTable(buildInfo, output, options={}) {
    /*
     * Load the "allocation table" for a particular build output.
     * 
     * Args:
     * - buildId: The PK of the Build object
     * - partId: The PK of the Part object
     * - output: The StockItem object which is the "output" of the build
     * - options:
     * -- table: The #id of the table (will be auto-calculated if not provided)
     */

    var buildId = buildInfo.pk;
    var partId = buildInfo.part;

    var outputId = null;
    
    outputId = output.pk;

    var table = options.table;
    
    if (options.table == null) {
        table = `#allocation-table-${outputId}`;
    }
    
    function reloadTable() {
        // Reload the entire build allocation table
        $(table).bootstrapTable('refresh');
    }

    function requiredQuantity(row) {
        // Return the requied quantity for a given row

        return row.quantity * output.quantity;
    }

    function sumAllocations(row) {
        // Calculat total allocations for a given row
        if (!row.allocations) {
            return 0;
        }

        var quantity = 0;

        row.allocations.forEach(function(item) {
            quantity += item.quantity;
        });

        return quantity;
    }

    function setupCallbacks() {
        // Register button callbacks once table data are loaded

        // Callback for 'allocate' button
        $(table).find(".button-add").click(function() {

            // Primary key of the 'sub_part'
            var pk = $(this).attr('pk');

            // Launch form to allocate new stock against this output
            launchModalForm("{% url 'build-item-create' %}", {
                success: reloadTable,
                data: {
                    part: pk,
                    build: buildId,
                    install_into: outputId,
                },
                secondary: [
                    {
                        field: 'stock_item',
                        label: '{% trans "New Stock Item" %}',
                        title: '{% trans "Create new Stock Item" %}',
                        url: '{% url "stock-item-create" %}',
                        data: {
                            part: pk,
                        },
                    },
                ],
                callback: [
                    {
                        field: 'stock_item',
                        action: function(value) {
                            inventreeGet(
                                `/api/stock/${value}/`, {},
                                {
                                    success: function(response) {

                                        // How many items are actually available for the given stock item?
                                        var available = response.quantity - response.allocated;

                                        var field = getFieldByName('#modal-form', 'quantity');

                                        // Allocation quantity initial value
                                        var initial = field.attr('value');

                                        if (available < initial) {
                                            field.val(available);
                                        }
                                    }
                                }
                            )
                        }
                    }
                ]
            });
        });

        // Callback for 'buy' button
        $(table).find('.button-buy').click(function() {
            var pk = $(this).attr('pk');

            var idx = $(this).closest('tr').attr('data-index');
            var row = $(table).bootstrapTable('getData')[idx];

            launchModalForm('{% url "order-parts" %}', {
                data: {
                    parts: [
                        pk,
                    ]
                }
            });
        });

        // Callback for 'build' button
        $(table).find('.button-build').click(function() {
            var pk = $(this).attr('pk');

            // Extract row data from the table
            var idx = $(this).closest('tr').attr('data-index');
            var row = $(table).bootstrapTable('getData')[idx];

            // Launch form to create a new build order
            launchModalForm('{% url "build-create" %}', {
                follow: true,
                data: {
                    part: pk,
                    parent: buildId,
                    quantity: requiredQuantity(row) - sumAllocations(row),
                }
            });
        });

        // Callback for 'unallocate' button
        $(table).find('.button-unallocate').click(function() {
            var pk = $(this).attr('pk');

            launchModalForm(`/build/${buildId}/unallocate/`,
                {
                    success: reloadTable,
                    data: {
                        output: outputId,
                        part: pk,
                    }
                }
            );
        });
    }

    // Load table of BOM items
    $(table).inventreeTable({
        url: "{% url 'api-bom-list' %}",
        queryParams: {
            part: partId,
            sub_part_detail: true,
        },
        formatNoMatches: function() { 
            return '{% trans "No BOM items found" %}';
        },
        name: 'build-allocation',
        uniqueId: 'sub_part',
        onPostBody: setupCallbacks,
        onLoadSuccess: function(tableData) {
            // Once the BOM data are loaded, request allocation data for this build output

            inventreeGet('/api/build/item/',
                {
                    build: buildId,
                    output: outputId,
                },
                {
                    success: function(data) {
                        // Iterate through the returned data, and group by the part they point to
                        var allocations = {};

                        // Total number of line items
                        var totalLines = tableData.length;

                        // Total number of "completely allocated" lines
                        var allocatedLines = 0;

                        data.forEach(function(item) {

                            // Group BuildItem objects by part
                            var part = item.part;
                            var key = parseInt(part);

                            if (!(key in allocations)) {
                                allocations[key] = new Array();
                            }

                            allocations[key].push(item);
                        });

                        // Now update the allocations for each row in the table
                        for (var key in allocations) {

                            // Select the associated row in the table
                            var tableRow = $(table).bootstrapTable('getRowByUniqueId', key);

                            if (!tableRow) {
                                continue;
                            }

                            // Set the allocation list for that row
                            tableRow.allocations = allocations[key];

                            // Calculate the total allocated quantity
                            var allocatedQuantity = sumAllocations(tableRow);

                            // Is this line item fully allocated?
                            if (allocatedQuantity >= (tableRow.quantity * output.quantity)) {
                                allocatedLines += 1;
                            }

                            // Push the updated row back into the main table
                            $(table).bootstrapTable('updateByUniqueId', key, tableRow, true);
                        }

                        // Update the total progress for this build output
                        var buildProgress = $(`#allocation-panel-${outputId}`).find($(`#output-progress-${outputId}`));

                        var progress = makeProgressBar(
                            allocatedLines,
                            totalLines
                        );

                        buildProgress.html(progress);

                        // Update the available actions for this build output

                        makeBuildOutputActionButtons(output, buildInfo);
                    }
                }
            );
        },
        sortable: true,
        showColumns: false,
        detailViewByClick: true,
        detailView: true,
        detailFilter: function(index, row) {
            return row.allocations != null;
        },
        detailFormatter: function(index, row, element) {
            // Contruct an 'inner table' which shows which stock items have been allocated

            var subTableId = `allocation-table-${row.pk}`;

            var html = `<div class='sub-table'><table class='table table-condensed table-striped' id='${subTableId}'></table></div>`;

            element.html(html);

            var lineItem = row;

            var subTable = $(`#${subTableId}`);

            subTable.bootstrapTable({
                data: row.allocations,
                showHeader: true,
                columns: [
                    {
                        width: '50%',
                        field: 'quantity',
                        title: '{% trans "Assigned Stock" %}',
                        formatter: function(value, row, index, field) {
                            var text = '';

                            var url = '';

                            if (row.serial && row.quantity == 1) {
                                text = `{% trans "Serial Number" %}: ${row.serial}`;
                            } else {
                                text = `{% trans "Quantity" %}: ${row.quantity}`;
                            }

                            {% if build.status == BuildStatus.COMPLETE %}
                            url = `/stock/item/${row.pk}/`;
                            {% else %}
                            url = `/stock/item/${row.stock_item}/`;
                            {% endif %}

                            return renderLink(text, url);
                        }
                    },
                    {
                        field: 'location',
                        title: '{% trans "Location" %}',
                        formatter: function(value, row, index, field) {
                            if (row.stock_item_detail.location) {
                                var text = row.stock_item_detail.location_name;
                                var url = `/stock/location/${row.stock_item_detail.location}/`;
                                
                                return renderLink(text, url);
                            } else {
                                return '<i>{% trans "No location set" %}</i>';
                            }
                        }
                    },
                    {
                        field: 'actions',
                        formatter: function(value, row, index, field) {
                            /* Actions available for a particular stock item allocation:
                             * 
                             * - Edit the allocation quantity
                             * - Delete the allocation
                             */

                            var pk = row.pk;

                            var html = `<div class='btn-group float-right' role='group'>`;

                            html += makeIconButton('fa-edit icon-blue', 'button-allocation-edit', pk, '{% trans "Edit stock allocation" %}');

                            html += makeIconButton('fa-trash-alt icon-red', 'button-allocation-delete', pk, '{% trans "Delete stock allocation" %}');

                            html += `</div>`;

                            return html;
                        }
                    }
                ]
            });

            // Assign button callbacks to the newly created allocation buttons
            subTable.find('.button-allocation-edit').click(function() {
                var pk = $(this).attr('pk');
                launchModalForm(`/build/item/${pk}/edit/`, {
                    success: reloadTable,
                });
            });

            subTable.find('.button-allocation-delete').click(function() {
                var pk = $(this).attr('pk');
                launchModalForm(`/build/item/${pk}/delete/`, {
                    success: reloadTable,
                });
            });
        },
        columns: [
            {
                field: 'pk',
                visible: false,
            },
            {
                field: 'sub_part_detail.full_name',
                title: '{% trans "Required Part" %}',
                sortable: true,
                formatter: function(value, row, index, field) {
                    var url = `/part/${row.sub_part}/`;
                    var thumb = row.sub_part_detail.thumbnail;
                    var name = row.sub_part_detail.full_name;

                    var html = imageHoverIcon(thumb) + renderLink(name, url);

                    html += makePartIcons(row.sub_part_detail);

                    return html;
                }
            },
            {
                field: 'reference',
                title: '{% trans "Reference" %}',
                sortable: true,
            },
            {
                field: 'quantity',
                title: '{% trans "Quantity Per" %}',
                sortable: true,
            },
            {
                field: 'sub_part_detail.stock',
                title: '{% trans "Available" %}',
            },
            {
                field: 'allocated',
                title: '{% trans "Allocated" %}',
                sortable: true,
                formatter: function(value, row, index, field) {
                    var allocated = 0;

                    if (row.allocations) {
                        row.allocations.forEach(function(item) {
                            allocated += item.quantity;
                        });
                    }

                    var required = requiredQuantity(row);

                    return makeProgressBar(allocated, required);
                },
                sorter: function(valA, valB, rowA, rowB) {
                    var aA = sumAllocations(rowA);
                    var aB = sumAllocations(rowB);

                    var qA = rowA.quantity;
                    var qB = rowB.quantity;

                    qA *= output.quantity;
                    qB *= output.quantity;
                
                    // Handle the case where both numerators are zero
                    if ((aA == 0) && (aB == 0)) {
                        return (qA > qB) ? 1 : -1;
                    }

                    // Handle the case where either denominator is zero
                    if ((qA == 0) || (qB == 0)) {
                        return 1;
                    }
                    
                    var progressA = parseFloat(aA) / qA;
                    var progressB = parseFloat(aB) / qB;

                    // Handle the case where both ratios are equal
                    if (progressA == progressB) {
                        return (qA < qB) ? 1 : -1;
                    }
    
                    return (progressA < progressB) ? 1 : -1;
                }
            },
            {
                field: 'actions',
                title: '{% trans "Actions" %}',
                formatter: function(value, row, index, field) {
                    // Generate action buttons for this build output
                    var html = `<div class='btn-group float-right' role='group'>`;

                    if (sumAllocations(row) < requiredQuantity(row)) {
                        if (row.sub_part_detail.assembly) {
                            html += makeIconButton('fa-tools icon-blue', 'button-build', row.sub_part, '{% trans "Build stock" %}');
                        }

                        if (row.sub_part_detail.purchaseable) {
                            html += makeIconButton('fa-shopping-cart icon-blue', 'button-buy', row.sub_part, '{% trans "Order stock" %}');
                        }

                        html += makeIconButton('fa-sign-in-alt icon-green', 'button-add', row.sub_part, '{% trans "Allocate stock" %}');
                    }

                    html += makeIconButton(
                        'fa-minus-circle icon-red', 'button-unallocate', row.sub_part,
                        '{% trans "Unallocate stock" %}',
                        {
                            disabled: row.allocations == null
                        }
                    );

                    html += '</div>';

                    return html;
                }
            },
        ]
    });
}


function loadBuildTable(table, options) {
    // Display a table of Build objects

    var params = options.params || {};

    var filters = {};
    
    if (!options.disableFilters) {
        filters = loadTableFilters("build");
    }

    for (var key in params) {
        filters[key] = params[key];
    }

    setupFilterList("build", table);

    $(table).inventreeTable({
        method: 'get',
        formatNoMatches: function() {
            return '{% trans "No builds matching query" %}';
        },
        url: options.url,
        queryParams: filters,
        groupBy: false,
        name: 'builds',
        original: params,
        columns: [
            {
                field: 'pk',
                title: 'ID', 
                visible: false,
                switchable: false,
            },
            {
                field: 'reference',
                title: '{% trans "Build" %}',
                sortable: true,
                switchable: false,
                formatter: function(value, row, index, field) {

                    var prefix = "{% settings_value 'BUILDORDER_REFERENCE_PREFIX' %}";

                    if (prefix) {
                        value = `${prefix}${value}`;
                    }

                    var html = renderLink(value, '/build/' + row.pk + '/');

                    if (row.overdue) {
                        html += makeIconBadge('fa-calendar-times icon-red', '{% trans "Build order is overdue" %}');
                    }

                    return html;
                }
            },
            {
                field: 'title',
                title: '{% trans "Description" %}',
                sortable: true,
            },
            {
                field: 'part',
                title: '{% trans "Part" %}',
                sortable: true,
                formatter: function(value, row, index, field) {

                    var html = imageHoverIcon(row.part_detail.thumbnail);

                    html += renderLink(row.part_detail.full_name, `/part/${row.part}/`);
                    html += makePartIcons(row.part_detail);

                    return html;
                }
            },
            {
                field: 'quantity',
                title: '{% trans "Completed" %}',
                sortable: true,
                formatter: function(value, row, index, field) {
                    return makeProgressBar(
                        row.completed,
                        row.quantity,
                        {
                            //style: 'max',
                        }
                    );
                }
            },
            {
                field: 'status',
                title: '{% trans "Status" %}',
                sortable: true,
                formatter: function(value, row, index, field) {
                    return buildStatusDisplay(value);
                },
            },
            {
                field: 'creation_date',
                title: '{% trans "Created" %}',
                sortable: true,
            },
            {
                field: 'target_date',
                title: '{% trans "Target Date" %}',
                sortable: true,
            },
            {
                field: 'completion_date',
                title: '{% trans "Completed" %}',
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
        formatNoMatches: function() { return '{% trans "No parts allocated for" %} ' + part; },
        columns: [
            {
                field: 'stock_item_detail',
                title: '{% trans "Stock Item" %}',
                formatter: function(value, row, index, field) {
                    return '' + parseFloat(value.quantity) + ' x ' + value.part_name + ' @ ' + value.location_name;
                }
            },
            {
                field: 'stock_item_detail.quantity',
                title: '{% trans "Available" %}',
                formatter: function(value, row, index, field) {
                    return parseFloat(value);
                }
            },
            {
                field: 'quantity',
                title: '{% trans "Allocated" %}',
                formatter: function(value, row, index, field) {
                    var html = parseFloat(value);

                    var bEdit = "<button class='btn item-edit-button btn-sm' type='button' title='{% trans "Edit stock allocation" %}' url='/build/item/" + row.pk + "/edit/'><span class='fas fa-edit'></span></button>";
                    var bDel = "<button class='btn item-del-button btn-sm' type='button' title='{% trans "Delete stock allocation" %}' url='/build/item/" + row.pk + "/delete/'><span class='fas fa-trash-alt icon-red'></span></button>";
                    
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