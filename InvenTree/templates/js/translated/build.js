{% load i18n %}
{% load inventree_extras %}

/* globals
    buildStatusDisplay,
    constructForm,
    getFieldByName,
    global_settings,
    imageHoverIcon,
    inventreeGet,
    launchModalForm,
    linkButtonsToSelection,
    loadTableFilters,
    makeIconBadge,
    makeIconButton,
    makePartIcons,
    makeProgressBar,
    renderLink,
    setupFilterList,
*/

/* exported
    editBuildOrder,
    loadAllocationTable,
    loadBuildOrderAllocationTable,
    loadBuildOutputAllocationTable,
    loadBuildPartsTable,
    loadBuildTable,
*/


function buildFormFields() {
    return {
        reference: {
            prefix: global_settings.BUILDORDER_REFERENCE_PREFIX,
        },
        title: {},
        part: {},
        quantity: {},
        parent: {
            filters: {
                part_detail: true,
            }
        },
        batch: {},
        target_date: {},
        take_from: {},
        destination: {},
        link: {
            icon: 'fa-link',
        },
        issued_by: {
            icon: 'fa-user',
        },
        responsible: {
            icon: 'fa-users',
        },
    };
}


function editBuildOrder(pk) {

    var fields = buildFormFields();

    constructForm(`/api/build/${pk}/`, {
        fields: fields,
        reload: true,
        title: '{% trans "Edit Build Order" %}',
    });
}

function newBuildOrder(options={}) {
    /* Launch modal form to create a new BuildOrder.
     */

    var fields = buildFormFields();

    if (options.part) {
        fields.part.value = options.part;
    }

    if (options.quantity) {
        fields.quantity.value = options.quantity;
    }

    if (options.parent) {
        fields.parent.value = options.parent;
    }

    constructForm(`/api/build/`, {
        fields: fields,
        follow: true,
        method: 'POST',
        title: '{% trans "Create Build Order" %}'
    });
}


function makeBuildOutputActionButtons(output, buildInfo, lines) {
    /* Generate action buttons for a build output.
     */

    var buildId = buildInfo.pk;

    var outputId = 'untracked';

    if (output) {
        outputId = output.pk;
    }

    var panel = `#allocation-panel-${outputId}`;

    function reloadTable() {
        $(panel).find(`#allocation-table-${outputId}`).bootstrapTable('refresh');
    }

    // Find the div where the buttons will be displayed
    var buildActions = $(panel).find(`#output-actions-${outputId}`);

    var html = `<div class='btn-group float-right' role='group'>`;

    // "Auto" allocation only works for untracked stock items
    if (!output && lines > 0) {
        html += makeIconButton(
            'fa-magic icon-blue', 'button-output-auto', outputId,
            '{% trans "Auto-allocate stock items to this output" %}',
        );
    }

    if (lines > 0) {
        // Add a button to "cancel" the particular build output (unallocate)
        html += makeIconButton(
            'fa-minus-circle icon-red', 'button-output-unallocate', outputId,
            '{% trans "Unallocate stock from build output" %}',
        );
    }


    if (output) {

        // Add a button to "complete" the particular build output
        html += makeIconButton(
            'fa-check icon-green', 'button-output-complete', outputId,
            '{% trans "Complete build output" %}',
            {
                // disabled: true
            }
        );

        // Add a button to "delete" the particular build output
        html += makeIconButton(
            'fa-trash-alt icon-red', 'button-output-delete', outputId,
            '{% trans "Delete build output" %}',
        );

        // TODO - Add a button to "destroy" the particular build output (mark as damaged, scrap)
    }

    html += '</div>';

    buildActions.html(html);

    // Add callbacks for the buttons
    $(panel).find(`#button-output-auto-${outputId}`).click(function() {
        // Launch modal dialog to perform auto-allocation
        launchModalForm(`/build/${buildId}/auto-allocate/`,
            {
                data: {
                },
                success: reloadTable,
            }
        );
    });

    $(panel).find(`#button-output-complete-${outputId}`).click(function() {

        var pk = $(this).attr('pk');

        launchModalForm(
            `/build/${buildId}/complete-output/`,
            {
                data: {
                    output: pk,
                },
                reload: true,
            }
        );  
    });

    $(panel).find(`#button-output-unallocate-${outputId}`).click(function() {

        var pk = $(this).attr('pk');

        launchModalForm(
            `/build/${buildId}/unallocate/`,
            {
                success: reloadTable,
                data: {
                    output: pk,
                }
            }
        );
    });

    $(panel).find(`#button-output-delete-${outputId}`).click(function() {

        var pk = $(this).attr('pk');

        launchModalForm(
            `/build/${buildId}/delete-output/`,
            {
                reload: true,
                data: {
                    output: pk
                }
            }
        );
    });
}


function loadBuildOrderAllocationTable(table, options={}) {
    /**
     * Load a table showing all the BuildOrder allocations for a given part
     */

    options.params['part_detail'] = true;
    options.params['build_detail'] = true;
    options.params['location_detail'] = true;

    var filters = loadTableFilters('buildorderallocation');

    for (var key in options.params) {
        filters[key] = options.params[key];
    }

    setupFilterList('buildorderallocation', $(table));

    $(table).inventreeTable({
        url: '{% url "api-build-item-list" %}',
        queryParams: filters,
        name: 'buildorderallocation',
        groupBy: false,
        search: false,
        paginationVAlign: 'bottom',
        original: options.params,
        formatNoMatches: function() {
            return '{% trans "No build order allocations found" %}';
        },
        columns: [
            {
                field: 'pk',
                visible: false,
                switchable: false,
            },
            {
                field: 'build',
                switchable: false,
                title: '{% trans "Build Order" %}',
                formatter: function(value, row) {
                    var prefix = global_settings.BUILDORDER_REFERENCE_PREFIX;

                    var ref = `${prefix}${row.build_detail.reference}`;

                    return renderLink(ref, `/build/${row.build}/`);
                }
            },
            {
                field: 'item',
                title: '{% trans "Stock Item" %}',
                formatter: function(value, row) {
                    // Render a link to the particular stock item

                    var link = `/stock/item/${row.stock_item}/`;
                    var text = `{% trans "Stock Item" %} ${row.stock_item}`;

                    return renderLink(text, link);
                }
            },
            {
                field: 'location',
                title: '{% trans "Location" %}',
                formatter: function(value, row) {

                    if (!value) {
                        return '{% trans "Location not specified" %}';
                    }
                    
                    var link = `/stock/location/${value}`;
                    var text = row.location_detail.description;

                    return renderLink(text, link);
                }
            },
            {
                field: 'quantity',
                title: '{% trans "Quantity" %}',
                sortable: true,
            }
        ]
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

    if (output) {
        outputId = output.pk;
    } else {
        outputId = 'untracked';
    }

    var table = options.table;

    if (options.table == null) {
        table = `#allocation-table-${outputId}`;
    }

    // If an "output" is specified, then only "trackable" parts are allocated
    // Otherwise, only "untrackable" parts are allowed
    var trackable = ! !output;

    function reloadTable() {
        // Reload the entire build allocation table
        $(table).bootstrapTable('refresh');
    }

    function requiredQuantity(row) {
        // Return the requied quantity for a given row

        if (output) {
            // "Tracked" parts are calculated against individual build outputs
            return row.quantity * output.quantity;
        } else {
            // "Untracked" parts are specified against the build itself
            return row.quantity * buildInfo.quantity;
        }
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
        $(table).find('.button-add').click(function() {

            // Primary key of the 'sub_part'
            var pk = $(this).attr('pk');

            // Launch form to allocate new stock against this output
            launchModalForm('{% url "build-item-create" %}', {
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
                            );
                        }
                    }
                ]
            });
        });

        // Callback for 'buy' button
        $(table).find('.button-buy').click(function() {

            var pk = $(this).attr('pk');

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

            newBuildOrder({
                part: pk,
                parent: buildId,
                quantity: requiredQuantity(row) - sumAllocations(row),
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
        url: '{% url "api-bom-list" %}',
        queryParams: {
            part: partId,
            sub_part_detail: true,
            sub_part_trackable: trackable,
        },
        disablePagination: true,
        formatNoMatches: function() { 
            return '{% trans "No BOM items found" %}';
        },
        name: 'build-allocation',
        uniqueId: 'sub_part',
        onPostBody: setupCallbacks,
        onLoadSuccess: function(tableData) {
            // Once the BOM data are loaded, request allocation data for this build output

            var params = {
                build: buildId,
                part_detail: true,
                location_detail: true,
            };

            if (output) {
                params.sub_part_trackable = true;
                params.output = outputId;
            } else {
                params.sub_part_trackable = false;
            }

            inventreeGet('/api/build/item/',
                params,
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
                            var part = item.bom_part || item.part;
                            var key = parseInt(part);

                            if (!(key in allocations)) {
                                allocations[key] = [];
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

                            var requiredQuantity = 0;

                            if (output) {
                                requiredQuantity = tableRow.quantity * output.quantity;
                            } else {
                                requiredQuantity = tableRow.quantity * buildInfo.quantity;
                            }

                            // Is this line item fully allocated?
                            if (allocatedQuantity >= requiredQuantity) {
                                allocatedLines += 1;
                            }

                            // Push the updated row back into the main table
                            $(table).bootstrapTable('updateByUniqueId', key, tableRow, true);
                        }

                        // Update the total progress for this build output
                        var buildProgress = $(`#allocation-panel-${outputId}`).find($(`#output-progress-${outputId}`));

                        if (totalLines > 0) {

                            var progress = makeProgressBar(
                                allocatedLines,
                                totalLines
                            );

                            buildProgress.html(progress);
                        } else {
                            buildProgress.html('');
                        }

                        // Update the available actions for this build output

                        makeBuildOutputActionButtons(output, buildInfo, totalLines);
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

            var subTable = $(`#${subTableId}`);

            subTable.bootstrapTable({
                data: row.allocations,
                showHeader: true,
                columns: [
                    {
                        field: 'part',
                        title: '{% trans "Part" %}',
                        formatter: function(value, row) {

                            var html = imageHoverIcon(row.part_detail.thumbnail);
                            html += renderLink(row.part_detail.full_name, `/part/${value}/`);
                            return html;
                        }
                    },
                    {
                        width: '50%',
                        field: 'quantity',
                        title: '{% trans "Assigned Stock" %}',
                        formatter: function(value, row) {
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
                        formatter: function(value, row) {
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
                        formatter: function(value, row) {
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
                visible: true,
                switchable: false,
                checkbox: true,
            },
            {
                field: 'sub_part_detail.full_name',
                title: '{% trans "Required Part" %}',
                sortable: true,
                formatter: function(value, row) {
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
                sortable: true,
            },
            {
                field: 'allocated',
                title: '{% trans "Allocated" %}',
                sortable: true,
                formatter: function(value, row) {
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
                    // Custom sorting function for progress bars
                    
                    var aA = sumAllocations(rowA);
                    var aB = sumAllocations(rowB);

                    var qA = requiredQuantity(rowA);
                    var qB = requiredQuantity(rowB);

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

                    if (progressA == progressB) return 0;

                    return (progressA < progressB) ? 1 : -1;
                }
            },
            {
                field: 'actions',
                title: '{% trans "Actions" %}',
                formatter: function(value, row) {
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

    // Initialize the action buttons
    makeBuildOutputActionButtons(output, buildInfo, 0);
}



/**
 * Allocate stock items to a build
 * 
 * arguments:
 * - buildId: ID / PK value for the build
 * - partId: ID / PK value for the part being built
 * 
 * options:
 *  - outputId: ID / PK of the associated build output (or null for untracked items)
 *  - parts: List of ID values for filtering against specific sub parts
 */
function allocateStockToBuild(buildId, partId, options={}) {

    // ID of the associated "build output" (or null)
    var outputId = options.output || null;

    // Extract list of BOM items (or empty list)
    var subPartIds = options.parts || [];

    var bomItemQueryParams = {
        part: partId,
        sub_part_detail: true,
        sub_part_trackable: outputId != null
    };

    inventreeGet(
        '{% url "api-bom-list" %}',
        bomItemQueryParams,
        {
            success: function(response) {

                // List of BOM item objects we are interested in
                var bomItems = [];

                for (var idx = 0; idx < response.length; idx++) {
                    var item = response[idx];

                    var subPartId = item.sub_part;

                    // Check if we are interested in this item
                    if (subPartIds.length > 0 && !subPartIds.includes(subPartId)) {
                        continue;
                    }

                    bomItems.push(item);
                }
            }
        }
    );
}



function loadBuildTable(table, options) {
    // Display a table of Build objects

    var params = options.params || {};

    var filters = {};

    params['part_detail'] = true;

    if (!options.disableFilters) {
        filters = loadTableFilters('build');
    }

    for (var key in params) {
        filters[key] = params[key];
    }

    options.url = options.url || '{% url "api-build-list" %}';

    var filterTarget = options.filterTarget || null;

    setupFilterList('build', table, filterTarget);

    $(table).inventreeTable({
        method: 'get',
        formatNoMatches: function() {
            return '{% trans "No builds matching query" %}';
        },
        url: options.url,
        queryParams: filters,
        groupBy: false,
        sidePagination: 'server',
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
                checkbox: true,
                title: '{% trans "Select" %}',
                searchable: false,
                switchable: false,
            },
            {
                field: 'reference',
                title: '{% trans "Build" %}',
                sortable: true,
                switchable: true,
                formatter: function(value, row) {

                    var prefix = global_settings.BUILDORDER_REFERENCE_PREFIX;

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
                switchable: true,
            },
            {
                field: 'part',
                title: '{% trans "Part" %}',
                sortable: true,
                sortName: 'part__name',
                formatter: function(value, row) {

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
                formatter: function(value, row) {
                    return makeProgressBar(
                        row.completed,
                        row.quantity,
                        {
                            // style: 'max',
                        }
                    );
                }
            },
            {
                field: 'status',
                title: '{% trans "Status" %}',
                sortable: true,
                formatter: function(value) {
                    return buildStatusDisplay(value);
                },
            },
            {
                field: 'creation_date',
                title: '{% trans "Created" %}',
                sortable: true,
            },
            {
                field: 'issued_by',
                title: '{% trans "Issued by" %}',
                sortable: true,
                formatter: function(value, row) {
                    if (value) {
                        return row.issued_by_detail.username;
                    } else {
                        return `<i>{% trans "No user information" %}</i>`;
                    }
                }
            },
            {
                field: 'responsible',
                title: '{% trans "Responsible" %}',
                sortable: true,
                formatter: function(value, row) {
                    if (value) {
                        return row.responsible_detail.name;
                    } else {
                        return '{% trans "No information" %}';
                    }
                }
            },
            {
                field: 'target_date',
                title: '{% trans "Target Date" %}',
                sortable: true,
            },
            {
                field: 'completion_date',
                title: '{% trans "Completion Date" %}',
                sortable: true,
            },
        ],
    });

    linkButtonsToSelection(
        table,
        [
            '#build-print-options',
        ]
    );
}


function updateAllocationTotal(id, count, required) {

    count = parseFloat(count);

    $('#allocation-total-'+id).html(count);

    var el = $('#allocation-panel-' + id);
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
        formatNoMatches: function() {
            return '{% trans "No parts allocated for" %} ' + part;
        },
        columns: [
            {
                field: 'stock_item_detail',
                title: '{% trans "Stock Item" %}',
                formatter: function(value) {
                    return '' + parseFloat(value.quantity) + ' x ' + value.part_name + ' @ ' + value.location_name;
                }
            },
            {
                field: 'stock_item_detail.quantity',
                title: '{% trans "Available" %}',
                formatter: function(value) {
                    return parseFloat(value);
                }
            },
            {
                field: 'quantity',
                title: '{% trans "Allocated" %}',
                formatter: function(value, row) {
                    var html = parseFloat(value);

                    var bEdit = `<button class='btn item-edit-button btn-sm' type='button' title='{% trans "Edit stock allocation" %}' url='/build/item/${row.pk}/edit/'><span class='fas fa-edit'></span></button>`;
                    var bDel = `<button class='btn item-del-button btn-sm' type='button' title='{% trans "Delete stock allocation" %}' url='/build/item/${row.pk}/delete/'><span class='fas fa-trash-alt icon-red'></span></button>`;

                    html += `
                    <div class='btn-group' style='float: right;'>
                        ${bEdit}
                        ${bDel}
                    </div>
                    `;

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

    table.on('load-success.bs.table', function() {
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


function loadBuildPartsTable(table, options={}) {
    /**
     * Display a "required parts" table for build view.
     * 
     * This is a simplified BOM view:
     * - Does not display sub-bom items
     * - Does not allow editing of BOM items
     * 
     * Options:
     * 
     * part: Part ID
     * build: Build ID
     * build_quantity: Total build quantity
     * build_remaining: Number of items remaining
     */

    // Query params
    var params = {
        sub_part_detail: true,
        part: options.part,
    };

    var filters = {};

    if (!options.disableFilters) {
        filters = loadTableFilters('bom');
    }

    setupFilterList('bom', $(table));

    for (var key in params) {
        filters[key] = params[key];
    }

    function setupTableCallbacks() {
        // Register button callbacks once the table data are loaded

        // Callback for 'buy' button
        $(table).find('.button-buy').click(function() {
            var pk = $(this).attr('pk');

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

            newBuildOrder({
                part: pk,
                parent: options.build,
            });
        });
    }

    var columns = [
        {
            field: 'sub_part',
            title: '{% trans "Part" %}',
            switchable: false,
            sortable: true,
            formatter: function(value, row) {
                var url = `/part/${row.sub_part}/`;
                var html = imageHoverIcon(row.sub_part_detail.thumbnail) + renderLink(row.sub_part_detail.full_name, url);

                var sub_part = row.sub_part_detail;

                html += makePartIcons(row.sub_part_detail);

                // Display an extra icon if this part is an assembly
                if (sub_part.assembly) {
                    var text = `<span title='{% trans "Open subassembly" %}' class='fas fa-stream label-right'></span>`;

                    html += renderLink(text, `/part/${row.sub_part}/bom/`);
                }

                return html;
            }
        },
        {
            field: 'sub_part_detail.description',
            title: '{% trans "Description" %}',
        },
        {
            field: 'reference',
            title: '{% trans "Reference" %}',
            searchable: true,
            sortable: true,
        },
        {
            field: 'quantity',
            title: '{% trans "Quantity" %}',
            sortable: true
        },
        {
            sortable: true,
            switchable: false,
            field: 'sub_part_detail.stock',
            title: '{% trans "Available" %}',
            formatter: function(value, row) {
                return makeProgressBar(
                    value,
                    row.quantity * options.build_remaining,
                    {
                        id: `part-progress-${row.part}`
                    }
                );
            },
            sorter: function(valA, valB, rowA, rowB) {
                if (rowA.received == 0 && rowB.received == 0) {
                    return (rowA.quantity > rowB.quantity) ? 1 : -1;
                }

                var progressA = parseFloat(rowA.sub_part_detail.stock) / (rowA.quantity * options.build_remaining);
                var progressB = parseFloat(rowB.sub_part_detail.stock) / (rowB.quantity * options.build_remaining);

                return (progressA < progressB) ? 1 : -1;
            }
        },
        {
            field: 'actions',
            title: '{% trans "Actions" %}',
            switchable: false,
            formatter: function(value, row) {

                // Generate action buttons against the part
                var html = `<div class='btn-group float-right' role='group'>`;

                if (row.sub_part_detail.assembly) {
                    html += makeIconButton('fa-tools icon-blue', 'button-build', row.sub_part, '{% trans "Build stock" %}');
                }

                if (row.sub_part_detail.purchaseable) {
                    html += makeIconButton('fa-shopping-cart icon-blue', 'button-buy', row.sub_part, '{% trans "Order stock" %}');
                }

                html += `</div>`;

                return html;
            }
        }
    ];

    table.inventreeTable({
        url: '{% url "api-bom-list" %}',
        showColumns: true,
        name: 'build-parts',
        sortable: true,
        search: true,
        onPostBody: setupTableCallbacks,
        rowStyle: function(row) {
            var classes = [];

            // Shade rows differently if they are for different parent parts
            if (row.part != options.part) {
                classes.push('rowinherited');
            }

            if (row.validated) {
                classes.push('rowvalid');
            } else {
                classes.push('rowinvalid');
            }

            return {
                classes: classes.join(' '),
            };
        },
        formatNoMatches: function() {
            return '{% trans "No BOM items found" %}';
        },
        clickToSelect: true,
        queryParams: filters,
        original: params,
        columns: columns,
    });    
}
