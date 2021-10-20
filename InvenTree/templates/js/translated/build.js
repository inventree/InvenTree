{% load i18n %}
{% load inventree_extras %}

/* globals
    buildStatusDisplay,
    constructForm,
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
    allocateStockToBuild,
    editBuildOrder,
    loadAllocationTable,
    loadBuildOrderAllocationTable,
    loadBuildOutputAllocationTable,
    loadBuildOutputTable,
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
        sales_order: {
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

    // Specify the target part
    if (options.part) {
        fields.part.value = options.part;
    }

    // Specify the desired quantity
    if (options.quantity) {
        fields.quantity.value = options.quantity;
    }

    // Specify the parent build order
    if (options.parent) {
        fields.parent.value = options.parent;
    }

    // Specify a parent sales order
    if (options.sales_order) {
        fields.sales_order.value = options.sales_order;
    }

    constructForm(`/api/build/`, {
        fields: fields,
        follow: true,
        method: 'POST',
        title: '{% trans "Create Build Order" %}',
        onSuccess: options.onSuccess,
    });
}


/*
 * Construct a set of output buttons for a particular build output
 */
function makeBuildOutputButtons(output_id, build_info, options={}) {
 
    var html = `<div class='btn-group float-right' role='group'>`;

    // Tracked parts? Must be individually allocated
    if (build_info.tracked_parts) {

        // Add a button to allocate stock against this build output
        html += makeIconButton(
            'fa-sign-in-alt icon-blue',
            'button-output-allocate',
            output_id,
            '{% trans "Allocate stock items to this build output" %}',
            {
                disabled: true,
            }
        );

        // Add a button to unallocate stock from this build output
        html += makeIconButton(
            'fa-minus-circle icon-red',
            'button-output-unallocate',
            output_id,
            '{% trans "Unallocate stock from build output" %}',
        );
    }

    // Add a button to "complete" this build output
    html += makeIconButton(
        'fa-check-circle icon-green',
        'button-output-complete',
        output_id,
        '{% trans "Complete build output" %}',
    );

    // Add a button to "delete" this build output
    html += makeIconButton(
        'fa-trash-alt icon-red',
        'button-output-delete',
        output_id,
        '{% trans "Delete build output" %}',
    );

    html += `</div>`;

    return html;

}


/*
 * Unallocate stock against a particular build order
 * 
 * Options:
 * - output: pk value for a stock item "build output"
 * - bom_item: pk value for a particular BOMItem (build item)
 */
function unallocateStock(build_id, options={}) {

    var url = `/api/build/${build_id}/unallocate/`;

    var html = `
    <div class='alert alert-block alert-warning'>
    {% trans "Are you sure you wish to unallocate stock items from this build?" %}
    </dvi>
    `;

    constructForm(url, {
        method: 'POST',
        confirm: true,
        preFormContent: html,
        fields: {
            output: {
                hidden: true,
                value: options.output,
            },
            bom_item: {
                hidden: true,
                value: options.bom_item,
            },
        },
        title: '{% trans "Unallocate Stock Items" %}',
        onSuccess: function(response, opts) {
            if (options.table) {
                // Reload the parent table
                $(options.table).bootstrapTable('refresh');
            }
        }
    });
}


/**
 * Launch a modal form to complete selected build outputs
 */
function completeBuildOutputs(build_id, outputs, options={}) {
    
    if (outputs.length == 0) {
        showAlertDialog(
            '{% trans "Select Build Outputs" %}',
            '{% trans "At least one build output must be selected" %}',
        );
        return;
    }

    // Render a single build output (StockItem)
    function renderBuildOutput(output, opts={}) {
        var pk = output.pk;

        var output_html = imageHoverIcon(output.part_detail.thumbnail);

        if (output.quantity == 1 && output.serial) {
            output_html += `{% trans "Serial Number" %}: ${output.serial}`;
        } else {
            output_html += `{% trans "Quantity" %}: ${output.quantity}`;
        }

        var buttons = `<div class='btn-group float-right' role='group'>`;

        buttons += makeIconButton('fa-times icon-red', 'button-row-remove', pk, '{% trans "Remove row" %}');

        buttons += '</div>';

        var field = constructField(
            `outputs_output_${pk}`,
            {
                type: 'raw',
                html: output_html,
            },
            {
                hideLabels: true,
            }
        );

        var html = `
        <tr id='output_row_${pk}'>
            <td>${field}</td>
            <td>${output.part_detail.full_name}</td>
            <td>${buttons}</td>
        </tr>`;

        return html;
    }

    // Construct table entries
    var table_entries = '';

    outputs.forEach(function(output) {
        table_entries += renderBuildOutput(output);
    });

    var html = `
    <table class='table table-striped table-condensed' id='build-complete-table'>
        <thead>
            <th colspan='2'>{% trans "Output" %}</th>
            <th><!-- Actions --></th>
        </thead>
        <tbody>
            ${table_entries}
        </tbody>
    </table>`;

    constructForm(`/api/build/${build_id}/complete/`, {
        method: 'POST',
        preFormContent: html,
        fields: {
            status: {},
            location: {},
        },
        confirm: true,
        title: '{% trans "Complete Build Outputs" %}',
        afterRender: function(fields, opts) {
            // Setup callbacks to remove outputs
            $(opts.modal).find('.button-row-remove').click(function() {
                var pk = $(this).attr('pk');

                $(opts.modal).find(`#output_row_${pk}`).remove();
            });
        },
        onSubmit: function(fields, opts) {
            
            // Extract data elements from the form
            var data = {
                outputs: [],
                status: getFormFieldValue('status', {}, opts),
                location: getFormFieldValue('location', {}, opts),
            };

            var output_pk_values = [];

            outputs.forEach(function(output) {
                var pk = output.pk;

                var row = $(opts.modal).find(`#output_row_${pk}`);

                if (row.exists()) {
                    data.outputs.push({
                        output: pk,
                    });
                    output_pk_values.push(pk);
                }
            });

            // Provide list of nested values
            opts.nested = {
                'outputs': output_pk_values,
            };

            inventreePut(
                opts.url,
                data,
                {
                    method: 'POST',
                    success: function(response) {
                        // Hide the modal
                        $(opts.modal).modal('hide');

                        if (options.success) {
                            options.success(response);
                        }
                    },
                    error: function(xhr) {
                        switch (xhr.status) {
                        case 400:
                            handleFormErrors(xhr.responseJSON, fields, opts);
                            break;
                        default:
                            $(opts.modal).modal('hide');
                            showApiError(xhr);
                            break;
                        }
                    }
                }
            );
        }
    });
}


/**
 * Load a table showing all the BuildOrder allocations for a given part
 */
function loadBuildOrderAllocationTable(table, options={}) {

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


/*
 * Display a "build output" table for a particular build.
 *
 * This displays a list of "active" (i.e. "in production") build outputs for a given build
 * 
 */
function loadBuildOutputTable(build_info, options={}) {

    var table = options.table || '#build-output-table';

    var params = options.params || {};

    // Mandatory query filters
    params.part_detail = true;
    params.is_building = true;
    params.build = build_info.pk;

    // Construct a list of "tracked" BOM items
    var tracked_bom_items = [];

    var has_tracked_items = false;

    build_info.bom_items.forEach(function(bom_item) {
        if (bom_item.sub_part_detail.trackable) {
            tracked_bom_items.push(bom_item);
            has_tracked_items = true;
        };
    });

    var filters = {};

    for (var key in params) {
        filters[key] = params[key];
    }

    // TODO: Initialize filter list

    function setupBuildOutputButtonCallbacks() {
        
        // Callback for the "allocate" button
        $(table).find('.button-output-allocate').click(function() {
            var pk = $(this).attr('pk');

            // Find the "allocation" sub-table associated with this output
            var subtable = $(`#output-sub-table-${pk}`);

            if (subtable.exists()) {
                var rows = subtable.bootstrapTable('getSelections');

                // None selected? Use all!
                if (rows.length == 0) {
                    rows = subtable.bootstrapTable('getData');
                }

                allocateStockToBuild(
                    build_info.pk,
                    build_info.part,
                    rows,
                    {
                        output: pk,
                        success: function() {
                            $(table).bootstrapTable('refresh');
                        }
                    }
                );
            } else {
                console.log(`WARNING: Could not locate sub-table for output ${pk}`);
            }
        });

        // Callack for the "unallocate" button
        $(table).find('.button-output-unallocate').click(function() {
            var pk = $(this).attr('pk');

            unallocateStock(build_info.pk, {
                output: pk,
                table: table
            });
        });

        // Callback for the "complete" button
        $(table).find('.button-output-complete').click(function() {
            var pk = $(this).attr('pk');

            var output = $(table).bootstrapTable('getRowByUniqueId', pk);

            completeBuildOutputs(
                build_info.pk,
                [
                    output,
                ],
                {
                    success: function() {
                        $(table).bootstrapTable('refresh');
                    }
                }
            );
        });

        // Callback for the "delete" button
        $(table).find('.button-output-delete').click(function() {
            var pk = $(this).attr('pk');

            // TODO: Move this to the API
            launchModalForm(
                `/build/${build_info.pk}/delete-output/`,
                {
                    data: {
                        output: pk
                    },
                    onSuccess: function() {
                        $(table).bootstrapTable('refresh');
                    }
                }
            );
        });
    }

    /*
     * Construct a "sub table" showing the required BOM items
     */
    function constructBuildOutputSubTable(index, row, element) {
        var sub_table_id = `output-sub-table-${row.pk}`;

        var html = `
        <div class='sub-table'>
            <table class='table table-striped table-condensed' id='${sub_table_id}'></table>
        </div>
        `;

        element.html(html);

        loadBuildOutputAllocationTable(
            build_info,
            row,
            {
                table: `#${sub_table_id}`,
                parent_table: table,
            }
        );
    }

    $(table).inventreeTable({
        url: '{% url "api-stock-list" %}',
        queryParams: filters,
        original: params,
        showColumns: false,
        uniqueId: 'pk',
        name: 'build-outputs',
        sortable: true,
        search: false,
        sidePagination: 'server',
        detailView: has_tracked_items,
        detailFilter: function(index, row) {
            return true;
        },
        detailFormatter: function(index, row, element) {
            constructBuildOutputSubTable(index, row, element);
        },
        formatNoMatches: function() {
            return '{% trans "No active build outputs found" %}';
        },
        onPostBody: function() {
            // Add callbacks for the buttons
            setupBuildOutputButtonCallbacks();

            $(table).bootstrapTable('expandAllRows');
        },
        columns: [
            {
                title: '',
                visible: true,
                checkbox: true,
                switchable: false,
            },
            {
                field: 'part',
                title: '{% trans "Part" %}',
                formatter: function(value, row) {
                    var thumb = row.part_detail.thumbnail;

                    return imageHoverIcon(thumb) + row.part_detail.full_name + makePartIcons(row.part_detail);
                }
            },
            {
                field: 'quantity',
                title: '{% trans "Quantity" %}',
                formatter: function(value, row) {

                    var url = `/stock/item/${row.pk}/`;

                    var text = '';

                    if (row.serial && row.quantity == 1) {
                        text = `{% trans "Serial Number" %}: ${row.serial}`;
                    } else {
                        text = `{% trans "Quantity" %}: ${row.quantity}`;
                    }

                    return renderLink(text, url);
                }
            },
            {
                field: 'allocated',
                title: '{% trans "Allocated Parts" %}',
                visible: has_tracked_items,
                formatter: function(value, row) {
                    return `<div id='output-progress-${row.pk}'><span class='fas fa-spin fa-spinner'></span></div>`;
                }
            },
            {
                field: 'actions',
                title: '',
                switchable: false,
                formatter: function(value, row) {
                    return makeBuildOutputButtons(
                        row.pk,
                        build_info,
                    );
                }
            }
        ]
    });

    // Enable the "allocate" button when the sub-table is exanded
    $(table).on('expand-row.bs.table', function(detail, index, row) {
        $(`#button-output-allocate-${row.pk}`).prop('disabled', false);
    });
    
    // Disable the "allocate" button when the sub-table is collapsed
    $(table).on('collapse-row.bs.table', function(detail, index, row) {
        $(`#button-output-allocate-${row.pk}`).prop('disabled', true);
    });
}


/*
 * Display the "allocation table" for a particular build output.
 * 
 * This displays a table of required allocations for a particular build output
 * 
 * Args:
 * - buildId: The PK of the Build object
 * - partId: The PK of the Part object
 * - output: The StockItem object which is the "output" of the build
 * - options:
 * -- table: The #id of the table (will be auto-calculated if not provided)
 */
function loadBuildOutputAllocationTable(buildInfo, output, options={}) {
    

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

    // Filters
    var filters = loadTableFilters('builditems');

    var params = options.params || {};

    for (var key in params) {
        filters[key] = params[key];
    }

    setupFilterList('builditems', $(table), options.filterTarget || null);

    // If an "output" is specified, then only "trackable" parts are allocated
    // Otherwise, only "untrackable" parts are allowed
    var trackable = ! !output;

    function reloadTable() {
        // Reload the entire build allocation table
        $(table).bootstrapTable('refresh');
    }

    function requiredQuantity(row) {
        // Return the requied quantity for a given row

        var quantity = 0;

        if (output) {
            // "Tracked" parts are calculated against individual build outputs
            quantity = row.quantity * output.quantity;
        } else {
            // "Untracked" parts are specified against the build itself
            quantity = row.quantity * buildInfo.quantity;
        }

        // Store the required quantity in the row data
        row.required = quantity;

        return quantity;
    }

    function sumAllocations(row) {
        // Calculat total allocations for a given row
        if (!row.allocations) {
            row.allocated = 0;
            return 0;
        }

        var quantity = 0;

        row.allocations.forEach(function(item) {
            quantity += item.quantity;
        });

        row.allocated = quantity;

        return quantity;
    }

    function setupCallbacks() {
        // Register button callbacks once table data are loaded

        // Callback for 'allocate' button
        $(table).find('.button-add').click(function() {

            // Primary key of the 'sub_part'
            var pk = $(this).attr('pk');

            // Extract BomItem information from this row
            var row = $(table).bootstrapTable('getRowByUniqueId', pk);

            if (!row) {
                console.log('WARNING: getRowByUniqueId returned null');
                return;
            }

            allocateStockToBuild(
                buildId,
                partId,
                [
                    row,
                ],
                {
                    source_location: buildInfo.source_location,
                    success: function(data) {
                        $(table).bootstrapTable('refresh');
                    },
                    output: output == null ? null : output.pk,
                }
            );
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

            // Extract row data from the table
            var idx = $(this).closest('tr').attr('data-index');
            var row = $(table).bootstrapTable('getData')[idx];

            unallocateStock(buildId, {
                bom_item: row.pk,
                output: outputId == 'untracked' ? null : outputId,
                table: table,
            });
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
        search: options.search || false,
        onPostBody: function(data) {
            // Setup button callbacks
            setupCallbacks();
        },
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

                        // Update the progress bar for this build output
                        var build_progress = $(`#output-progress-${outputId}`);

                        if (build_progress.exists()) {
                            if (totalLines > 0) {

                                var progress = makeProgressBar(
                                    allocatedLines,
                                    totalLines
                                );
    
                                build_progress.html(progress);
                            } else {
                                build_progress.html('');
                            }
    
                        } else {
                            console.log(`WARNING: Could not find progress bar for output ${outputId}`);
                        }
                    }
                }
            );
        },
        sortable: true,
        showColumns: false,
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


                            var serial = row.serial;

                            if (row.stock_item_detail) {
                                serial = row.stock_item_detail.serial;
                            }

                            if (serial && row.quantity == 1) {
                                text = `{% trans "Serial Number" %}: ${serial}`;
                            } else {
                                text = `{% trans "Quantity" %}: ${row.quantity}`;
                            }

                            var pk = row.stock_item || row.pk;

                            url = `/stock/item/${pk}/`;

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

                constructForm(`/api/build/item/${pk}/`, {
                    fields: {
                        quantity: {},
                    },
                    title: '{% trans "Edit Allocation" %}',
                    onSuccess: reloadTable,
                });
            });

            subTable.find('.button-allocation-delete').click(function() {
                var pk = $(this).attr('pk');

                constructForm(`/api/build/item/${pk}/`, {
                    method: 'DELETE',
                    title: '{% trans "Remove Allocation" %}',
                    onSuccess: reloadTable,
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

                    if (row.substitutes && row.substitutes.length > 0) {
                        html += makeIconBadge('fa-exchange-alt', '{% trans "Substitute parts available" %}');
                    }

                    if (row.allow_variants) {
                        html += makeIconBadge('fa-sitemap', '{% trans "Variant stock allowed" %}');
                    }

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
}



/**
 * Allocate stock items to a build
 * 
 * arguments:
 * - buildId: ID / PK value for the build
 * - partId: ID / PK value for the part being built
 * - bom_items: A list of BomItem objects to be allocated
 * 
 * options:
 *  - output: ID / PK of the associated build output (or null for untracked items)
 *  - source_location: ID / PK of the top-level StockLocation to take parts from (or null)
 */
function allocateStockToBuild(build_id, part_id, bom_items, options={}) {

    // ID of the associated "build output" (or null)
    var output_id = options.output || null;

    var source_location = options.source_location;

    function renderBomItemRow(bom_item, quantity) {

        var pk = bom_item.pk;
        var sub_part = bom_item.sub_part_detail;

        var thumb = thumbnailImage(bom_item.sub_part_detail.thumbnail);

        var delete_button = `<div class='btn-group float-right' role='group'>`;

        delete_button += makeIconButton(
            'fa-times icon-red',
            'button-row-remove',
            pk,
            '{% trans "Remove row" %}',
        );

        delete_button += `</div>`;

        var quantity_input = constructField(
            `items_quantity_${pk}`,
            {
                type: 'decimal',
                min_value: 0,
                value: quantity || 0,
                title: '{% trans "Specify stock allocation quantity" %}',
                required: true,
            },
            {
                hideLabels: true,
            }
        );

        var allocated_display = makeProgressBar(
            bom_item.allocated,
            bom_item.required,
        );

        var stock_input = constructField(
            `items_stock_item_${pk}`,
            {
                type: 'related field',
                required: 'true',
            },
            {
                hideLabels: true,
            }
        );

        // var stock_input = constructRelatedFieldInput(`items_stock_item_${pk}`);

        var html = `
        <tr id='allocation_row_${pk}' class='part-allocation-row'>
            <td id='part_${pk}'>
                ${thumb} ${sub_part.full_name}
            </td>
            <td id='allocated_${pk}'>
                ${allocated_display}
            </td>
            <td id='stock_item_${pk}'>
                ${stock_input}
            </td>
            <td id='quantity_${pk}'>
                ${quantity_input}
            </td>
            <td id='buttons_${pk}'>
                ${delete_button}
            </td>
        </tr>
        `;

        return html;
    }

    var table_entries = '';

    for (var idx = 0; idx < bom_items.length; idx++) {
        var bom_item = bom_items[idx];

        var required = bom_item.required || 0;
        var allocated = bom_item.allocated || 0;
        var remaining = required - allocated;

        if (remaining < 0) {
            remaining = 0;
        }

        // We only care about entries which are not yet fully allocated
        if (remaining > 0) {
            table_entries += renderBomItemRow(bom_item, remaining);
        }
    }

    if (table_entries.length == 0) {

        showAlertDialog(
            '{% trans "Select Parts" %}',
            '{% trans "You must select at least one part to allocate" %}',
        );

        return;
    }

    var html = ``;

    // Render a "take from" input
    html += constructField(
        'take_from',
        {
            type: 'related field',
            label: '{% trans "Source Location" %}',
            help_text: '{% trans "Select source location (leave blank to take from all locations)" %}',
            required: false,
        },
        {},
    );

    // Create table of parts
    html += `
    <table class='table table-striped table-condensed' id='stock-allocation-table'>
        <thead>
            <tr>
                <th>{% trans "Part" %}</th>
                <th>{% trans "Allocated" %}</th>
                <th style='min-width: 250px;'>{% trans "Stock Item" %}</th>
                <th>{% trans "Quantity" %}</th>
                <th></th>
            </tr>
        </thead>
        <tbody>
            ${table_entries}
        </tbody>
    </table>
    `;
              
    constructForm(`/api/build/${build_id}/allocate/`, {
        method: 'POST',
        fields: {},
        preFormContent: html,
        confirm: true,
        confirmMessage: '{% trans "Confirm stock allocation" %}',
        title: '{% trans "Allocate Stock Items to Build Order" %}',
        afterRender: function(fields, options) {

            var take_from_field = {
                name: 'take_from',
                model: 'stocklocation',
                api_url: '{% url "api-location-list" %}',
                required: false,
                type: 'related field',
                value: source_location,
                noResults: function(query) {
                    return '{% trans "No matching stock locations" %}';
                },
            };

            // Initialize "take from" field
            initializeRelatedField(
                take_from_field,
                null,
                options,
            );

            // Initialize stock item fields
            bom_items.forEach(function(bom_item) {
                initializeRelatedField(
                    {
                        name: `items_stock_item_${bom_item.pk}`,
                        api_url: '{% url "api-stock-list" %}',
                        filters: {
                            bom_item: bom_item.pk,
                            in_stock: true,
                            part_detail: true,
                            location_detail: true,
                        },
                        model: 'stockitem',
                        required: true,
                        render_part_detail: true,
                        render_location_detail: true,
                        auto_fill: true,
                        onSelect: function(data, field, opts) {
                            // Adjust the 'quantity' field based on availability

                            if (!('quantity' in data)) {
                                return;
                            }

                            // Quantity remaining to be allocated
                            var remaining = Math.max((bom_item.required || 0) - (bom_item.allocated || 0), 0);

                            // Calculate the available quantity
                            var available = Math.max((data.quantity || 0) - (data.allocated || 0), 0);

                            // Maximum amount that we need
                            var desired = Math.min(available, remaining);

                            updateFieldValue(`items_quantity_${bom_item.pk}`, desired, {}, opts);
                        },
                        adjustFilters: function(filters) {
                            // Restrict query to the selected location
                            var location = getFormFieldValue(
                                'take_from',
                                {},
                                {
                                    modal: options.modal,
                                }
                            );

                            filters.location = location;
                            filters.cascade = true;
                            
                            return filters;
                        },
                        noResults: function(query) {
                            return '{% trans "No matching stock items" %}';
                        }
                    },
                    null,
                    options,
                );
            });

            // Add callback to "clear" button for take_from field
            addClearCallback(
                'take_from',
                take_from_field,
                options,
            );

            // Add button callbacks
            $(options.modal).find('.button-row-remove').click(function() {
                var pk = $(this).attr('pk');

                $(options.modal).find(`#allocation_row_${pk}`).remove();
            });
        },
        onSubmit: function(fields, opts) {

            // Extract elements from the form
            var data = {
                items: []
            };

            var item_pk_values = [];

            bom_items.forEach(function(item) {

                var quantity = getFormFieldValue(
                    `items_quantity_${item.pk}`,
                    {},
                    {
                        modal: opts.modal,
                    },
                );

                var stock_item = getFormFieldValue(
                    `items_stock_item_${item.pk}`,
                    {},
                    {
                        modal: opts.modal,
                    }
                );

                if (quantity != null) {
                    data.items.push({
                        bom_item: item.pk,
                        stock_item: stock_item,
                        quantity: quantity,
                        output: output_id,
                    });

                    item_pk_values.push(item.pk);
                }
            });

            // Provide nested values
            opts.nested = {
                'items': item_pk_values
            };

            inventreePut(
                opts.url,
                data,
                {
                    method: 'POST',
                    success: function(response) {
                        // Hide the modal
                        $(opts.modal).modal('hide');

                        if (options.success) {
                            options.success(response);
                        }
                    },
                    error: function(xhr) {
                        switch (xhr.status) {
                        case 400:
                            handleFormErrors(xhr.responseJSON, fields, opts);
                            break;
                        default:
                            $(opts.modal).modal('hide');
                            showApiError(xhr);
                            break;
                        }
                    }
                }
            );
        },
    });
}


/*
 * Display a table of Build orders
 */
function loadBuildTable(table, options) {

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
