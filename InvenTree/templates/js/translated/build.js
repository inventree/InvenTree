{% load js_i18n %}
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
    autoAllocateStockToBuild,
    cancelBuildOrder,
    completeBuildOrder,
    createBuildOutput,
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
        part: {
            filters: {
                assembly: true,
                virtual: false,
            }
        },
        title: {},
        quantity: {},
        parent: {
            filters: {
                part_detail: true,
            }
        },
        sales_order: {
            icon: 'fa-truck',
        },
        batch: {},
        target_date: {
            icon: 'fa-calendar-alt',
        },
        take_from: {
            icon: 'fa-sitemap',
        },
        destination: {
            icon: 'fa-sitemap',
        },
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


/* Construct a form to cancel a build order */
function cancelBuildOrder(build_id, options={}) {

    constructForm(
        `/api/build/${build_id}/cancel/`,
        {
            method: 'POST',
            title: '{% trans "Cancel Build Order" %}',
            confirm: true,
            fields: {
                remove_allocated_stock: {},
                remove_incomplete_outputs: {},
            },
            preFormContent: function(opts) {
                var html = `
                <div class='alert alert-block alert-info'>
                    {% trans "Are you sure you wish to cancel this build?" %}
                </div>`;

                if (opts.context.has_allocated_stock) {
                    html += `
                    <div class='alert alert-block alert-warning'>
                        {% trans "Stock items have been allocated to this build order" %}
                    </div>`;
                }

                if (opts.context.incomplete_outputs) {
                    html += `
                    <div class='alert alert-block alert-warning'>
                        {% trans "There are incomplete outputs remaining for this build order" %}
                    </div>`;
                }

                return html;
            },
            onSuccess: function(response) {
                handleFormSuccess(response, options);
            }
        }
    );
}


/* Construct a form to "complete" (finish) a build order */
function completeBuildOrder(build_id, options={}) {

    var url = `/api/build/${build_id}/finish/`;

    var fields = {
        accept_unallocated: {},
        accept_incomplete: {},
    };

    var html = '';

    if (options.allocated && options.completed) {
        html += `
        <div class='alert alert-block alert-success'>
        {% trans "Build order is ready to be completed" %}
        </div>`;
    } else {
        html += `
        <div class='alert alert-block alert-danger'>
        <strong>{% trans "Build Order is incomplete" %}</strong>
        </div>
        `;

        if (!options.allocated) {
            html += `<div class='alert alert-block alert-warning'>{% trans "Required stock has not been fully allocated" %}</div>`;
        }

        if (!options.completed) {
            html += `<div class='alert alert-block alert-warning'>{% trans "Required build quantity has not been completed" %}</div>`;
        }
    }

    // Hide particular fields if they are not required

    if (options.allocated) {
        delete fields.accept_unallocated;
    }

    if (options.completed) {
        delete fields.accept_incomplete;
    }

    constructForm(url, {
        fields: fields,
        reload: true,
        confirm: true,
        method: 'POST',
        title: '{% trans "Complete Build Order" %}',
        preFormContent: html,
    });
}


/*
 * Construct a new build output against the provided build
 */
function createBuildOutput(build_id, options) {

    // Request build order information from the server
    inventreeGet(
        `/api/build/${build_id}/`,
        {},
        {
            success: function(build) {

                var html = '';

                var trackable = build.part_detail.trackable;
                var remaining = Math.max(0, build.quantity - build.completed);

                var fields = {
                    quantity: {
                        value: remaining,
                    },
                    serial_numbers: {
                        hidden: !trackable,
                        required: options.trackable_parts || trackable,
                    },
                    batch_code: {},
                    auto_allocate: {
                        hidden: !trackable,
                    },
                };

                // Work out the next available serial numbers
                inventreeGet(`/api/part/${build.part}/serial-numbers/`, {}, {
                    success: function(data) {
                        if (data.next) {
                            fields.serial_numbers.placeholder = `{% trans "Next available serial number" %}: ${data.next}`;
                        } else if (data.latest) {
                            fields.serial_numbers.placeholder = `{% trans "Latest serial number" %}: ${data.latest}`;
                        }
                    },
                    async: false,
                });

                if (options.trackable_parts) {
                    html += `
                    <div class='alert alert-block alert-info'>
                        {% trans "The Bill of Materials contains trackable parts" %}.<br>
                        {% trans "Build outputs must be generated individually" %}.
                    </div>
                    `;
                }

                if (trackable) {
                    html += `
                    <div class='alert alert-block alert-info'>
                        {% trans "Trackable parts can have serial numbers specified" %}<br>
                        {% trans "Enter serial numbers to generate multiple single build outputs" %}
                    </div>
                    `;
                }

                constructForm(`/api/build/${build_id}/create-output/`, {
                    method: 'POST',
                    title: '{% trans "Create Build Output" %}',
                    confirm: true,
                    fields: fields,
                    preFormContent: html,
                    onSuccess: function(response) {
                        location.reload();
                    },
                });

            }
        }
    );

}


/*
 * Construct a set of output buttons for a particular build output
 */
function makeBuildOutputButtons(output_id, build_info, options={}) {

    var html = `<div class='btn-group float-right' role='group'>`;

    // Tracked parts? Must be individually allocated
    if (options.has_bom_items) {

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
            if (options.onSuccess) {
                options.onSuccess(response, opts);
            } else if (options.table) {
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
            notes: {},
            accept_incomplete_allocation: {},
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
                notes: getFormFieldValue('notes', {}, opts),
                accept_incomplete_allocation: getFormFieldValue('accept_incomplete_allocation', {type: 'boolean'}, opts),
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
                            showApiError(xhr, opts.url);
                            break;
                        }
                    }
                }
            );
        }
    });
}



/**
 * Launch a modal form to delete selected build outputs
 */
function deleteBuildOutputs(build_id, outputs, options={}) {

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

    constructForm(`/api/build/${build_id}/delete-outputs/`, {
        method: 'POST',
        preFormContent: html,
        fields: {},
        confirm: true,
        title: '{% trans "Delete Build Outputs" %}',
        afterRender: function(fields, opts) {
            // Setup callbacks to remove outputs
            $(opts.modal).find('.button-row-remove').click(function() {
                var pk = $(this).attr('pk');

                $(opts.modal).find(`#output_row_${pk}`).remove();
            });
        },
        onSubmit: function(fields, opts) {
            var data = {
                outputs: [],
            };

            var output_pk_values = [];

            outputs.forEach(function(output) {
                var pk = output.pk;

                var row = $(opts.modal).find(`#output_row_${pk}`);

                if (row.exists()) {
                    data.outputs.push({
                        output: pk
                    });
                    output_pk_values.push(pk);
                }
            });

            opts.nested = {
                'outputs': output_pk_values,
            };

            inventreePut(
                opts.url,
                data,
                {
                    method: 'POST',
                    success: function(response) {
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
                            showApiError(xhr, opts.url);
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


/* Internal helper functions for performing calculations on BOM data */

// Iterate through a list of allocations, returning *only* those which match a particular BOM row
function getAllocationsForBomRow(bom_row, allocations) {
    var part_id = bom_row.sub_part;

    var matching_allocations = [];

    allocations.forEach(function(allocation) {
        if (allocation.bom_part == part_id) {
            matching_allocations.push(allocation);
        }
    });

    return matching_allocations;
}

// Sum the allocation quantity for a given BOM row
function sumAllocationsForBomRow(bom_row, allocations) {
    var quantity = 0;

    getAllocationsForBomRow(bom_row, allocations).forEach(function(allocation) {
        quantity += allocation.quantity;
    });

    return formatDecimal(quantity, 10);
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

    var filters = {};

    for (var key in params) {
        filters[key] = params[key];
    }

    setupFilterList('builditems', $(table), options.filterTarget || '#filter-list-incompletebuilditems');

    function setupBuildOutputButtonCallbacks() {

        // Callback for the "allocate" button
        $(table).find('.button-output-allocate').click(function() {
            var pk = $(this).attr('pk');

            // Find the "allocation" sub-table associated with this output
            var subtable = $(`#output-sub-table-${pk}`);

            if (subtable.exists()) {
                var rows = getTableData(`#output-sub-table-${pk}`);

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
                console.warn(`Could not locate sub-table for output ${pk}`);
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
                        $('#build-stock-table').bootstrapTable('refresh');
                    }
                }
            );
        });

        // Callback for the "delete" button
        $(table).find('.button-output-delete').click(function() {
            var pk = $(this).attr('pk');

            var output = $(table).bootstrapTable('getRowByUniqueId', pk);

            deleteBuildOutputs(
                build_info.pk,
                [
                    output,
                ],
                {
                    success: function() {
                        $(table).bootstrapTable('refresh');
                        $('#build-stock-table').bootstrapTable('refresh');
                    }
                }
            );
        });
    }

    // List of "tracked bom items" required for this build order
    var bom_items = null;

    // Request list of BOM data for this build order
    inventreeGet(
        '{% url "api-bom-list" %}',
        {
            part: build_info.part,
            sub_part_detail: true,
            sub_part_trackable: true,
        },
        {
            async: false,
            success: function(response) {
                // Save the BOM items
                bom_items = response;
            }
        }
    );

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

        // Pass through the cached BOM items
        build_info.bom_items = bom_items;

        loadBuildOutputAllocationTable(
            build_info,
            row,
            {
                table: `#${sub_table_id}`,
                parent_table: table,
            }
        );
    }

    function updateAllocationData(rows) {
        // Update stock allocation information for the build outputs

        // Request updated stock allocation data for this build order
        inventreeGet(
            '{% url "api-build-item-list" %}',
            {
                build: build_info.pk,
                part_detail: true,
                location_detail: true,
                sub_part_trackable: true,
                tracked: true,
            },
            {
                success: function(response) {

                    // Group allocation information by the "install_into" field
                    var allocations = {};

                    response.forEach(function(allocation) {
                        var target = allocation.install_into;

                        if (target != null) {
                            if (!(target in allocations)) {
                                allocations[target] = [];
                            }

                            allocations[target].push(allocation);
                        }
                    });

                    // Now that the allocations have been grouped by stock item,
                    // we can update each row in the table,
                    // using the pk value of each row (stock item)
                    rows.forEach(function(row) {
                        row.allocations = allocations[row.pk] || [];
                        $(table).bootstrapTable('updateByUniqueId', row.pk, row, true);

                        var n_completed_lines = 0;

                        // Check how many BOM lines have been completely allocated for this build output
                        bom_items.forEach(function(bom_item) {

                            var required_quantity = bom_item.quantity * row.quantity;

                            if (sumAllocationsForBomRow(bom_item, row.allocations) >= required_quantity) {
                                n_completed_lines += 1;
                            }

                            var output_progress_bar = $(`#output-progress-${row.pk}`);

                            if (output_progress_bar.exists()) {
                                output_progress_bar.html(
                                    makeProgressBar(
                                        n_completed_lines,
                                        bom_items.length,
                                        {
                                            max_width: '150px',
                                        }
                                    )
                                );
                            }
                        });
                    });
                }
            }
        );
    }

    var part_tests = null;

    function updateTestResultData(rows) {
        // Update test result information for the build outputs

        // Request test template data if it has not already been retrieved
        if (part_tests == null) {
            inventreeGet(
                '{% url "api-part-test-template-list" %}',
                {
                    part: build_info.part,
                    required: true,
                },
                {
                    success: function(response) {
                        // Save the list of part tests
                        part_tests = response;

                        // Callback to this function again
                        updateTestResultData(rows);
                    }
                }
            );

            return;
        }

        // Retrieve stock results for the entire build
        inventreeGet(
            '{% url "api-stock-test-result-list" %}',
            {
                build: build_info.pk,
                ordering: '-date',
            },
            {
                success: function(results) {

                    // Iterate through each row and find matching test results
                    rows.forEach(function(row) {
                        var test_results = {};

                        results.forEach(function(result) {
                            if (result.stock_item == row.pk) {
                                // This test result matches the particular stock item

                                if (!(result.key in test_results)) {
                                    test_results[result.key] = result.result;
                                }
                            }
                        });

                        row.passed_tests = test_results;

                        $(table).bootstrapTable('updateByUniqueId', row.pk, row, true);
                    });
                }
            }
        );
    }

    // Return the number of 'passed' tests in a given row
    function countPassedTests(row) {
        if (part_tests == null) {
            return 0;
        }

        var results = row.passed_tests || {};
        var n = 0;

        part_tests.forEach(function(test) {
            if (results[test.key] || false) {
                n += 1;
            }
        });

        return n;
    }

    // Return the number of 'fully allocated' lines for a given row
    function countAllocatedLines(row) {
        var n_completed_lines = 0;

        bom_items.forEach(function(bom_row) {
            var required_quantity = bom_row.quantity * row.quantity;

            if (sumAllocationsForBomRow(bom_row, row.allocations || []) >= required_quantity) {
                n_completed_lines += 1;
            }
        });

        return n_completed_lines;
    }

    $(table).inventreeTable({
        url: '{% url "api-stock-list" %}',
        queryParams: filters,
        original: params,
        showColumns: true,
        uniqueId: 'pk',
        name: 'build-outputs',
        sortable: true,
        search: false,
        sidePagination: 'client',
        detailView: bom_items.length > 0,
        detailFilter: function(index, row) {
            return bom_items.length > 0;
        },
        detailFormatter: function(index, row, element) {
            constructBuildOutputSubTable(index, row, element);
        },
        formatNoMatches: function() {
            return '{% trans "No active build outputs found" %}';
        },
        onPostBody: function(rows) {
            // Add callbacks for the buttons
            setupBuildOutputButtonCallbacks();
        },
        onLoadSuccess: function(rows) {

            updateAllocationData(rows);
            updateTestResultData(rows);
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
                switchable: true,
                formatter: function(value, row) {
                    var thumb = row.part_detail.thumbnail;

                    return imageHoverIcon(thumb) + row.part_detail.full_name + makePartIcons(row.part_detail);
                }
            },
            {
                field: 'quantity',
                title: '{% trans "Build Output" %}',
                switchable: false,
                sortable: true,
                formatter: function(value, row) {

                    var url = `/stock/item/${row.pk}/`;

                    var text = '';

                    if (row.serial && row.quantity == 1) {
                        text = `{% trans "Serial Number" %}: ${row.serial}`;
                    } else {
                        text = `{% trans "Quantity" %}: ${row.quantity}`;
                    }

                    if (row.batch) {
                        text += ` <small>({% trans "Batch" %}: ${row.batch})</small>`;
                    }

                    return renderLink(text, url);
                },
                sorter: function(a, b, row_a, row_b) {
                    // Sort first by quantity, and then by serial number
                    if ((row_a.quantity > 1) || (row_b.quantity > 1)) {
                        return row_a.quantity > row_b.quantity ? 1 : -1;
                    }

                    if ((row_a.serial != null) && (row_b.serial != null)) {
                        var sn_a = Number.parseInt(row_a.serial) || 0;
                        var sn_b = Number.parseInt(row_b.serial) || 0;

                        return sn_a > sn_b ? 1 : -1;
                    }

                    return 0;
                }
            },
            {
                field: 'allocated',
                title: '{% trans "Allocated Stock" %}',
                visible: bom_items.length > 0,
                switchable: false,
                sortable: true,
                formatter: function(value, row) {

                    if (bom_items.length == 0) {
                        return `<div id='output-progress-${row.pk}'><em><small>{% trans "No tracked BOM items for this build" %}</small></em></div>`;
                    }

                    var progressBar = makeProgressBar(
                        countAllocatedLines(row),
                        bom_items.length,
                        {
                            max_width: '150px',
                        }
                    );

                    return `<div id='output-progress-${row.pk}'>${progressBar}</div>`;
                },
                sorter: function(value_a, value_b, row_a, row_b) {
                    var q_a = countAllocatedLines(row_a);
                    var q_b = countAllocatedLines(row_b);

                    return q_a > q_b ? 1 : -1;
                },
            },
            {
                field: 'tests',
                title: '{% trans "Completed Tests" %}',
                sortable: true,
                switchable: true,
                formatter: function(value, row) {
                    if (part_tests == null || part_tests.length == 0) {
                        return `<em><small>{% trans "No required tests for this build" %}</small></em>`;
                    }

                    var n_passed = countPassedTests(row);

                    var progress = makeProgressBar(
                        n_passed,
                        part_tests.length,
                        {
                            max_width: '150px',
                        }
                    );

                    return progress;
                },
                sorter: function(a, b, row_a, row_b) {
                    var n_a = countPassedTests(row_a);
                    var n_b = countPassedTests(row_b);

                    return n_a > n_b ? 1 : -1;
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
                        {
                            has_bom_items: bom_items.length > 0,
                        }
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

    // Add callbacks for the various table menubar buttons

    // Complete multiple outputs
    $('#multi-output-complete').click(function() {
        var outputs = getTableData(table);

        completeBuildOutputs(
            build_info.pk,
            outputs,
            {
                success: function() {
                    // Reload the "in progress" table
                    $('#build-output-table').bootstrapTable('refresh');

                    // Reload the "completed" table
                    $('#build-stock-table').bootstrapTable('refresh');
                }
            }
        );
    });

    // Delete multiple build outputs
    $('#multi-output-delete').click(function() {
        var outputs = getTableData(table);

        deleteBuildOutputs(
            build_info.pk,
            outputs,
            {
                success: function() {
                    // Reload the "in progress" table
                    $('#build-output-table').bootstrapTable('refresh');

                    // Reload the "completed" table
                    $('#build-stock-table').bootstrapTable('refresh');
                }
            }
        );
    });

    // Print stock item labels
    $('#incomplete-output-print-label').click(function() {
        var outputs = getTableData(table);

        var stock_id_values = [];

        outputs.forEach(function(output) {
            stock_id_values.push(output.pk);
        });

        printStockItemLabels(stock_id_values);
    });

    $('#outputs-expand').click(function() {
        $(table).bootstrapTable('expandAllRows');
    });

    $('#outputs-collapse').click(function() {
        $(table).bootstrapTable('collapseAllRows');
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

    var bom_items = buildInfo.bom_items || null;

    // If BOM items have not been provided, load via the API
    if (bom_items == null) {
        inventreeGet(
            '{% url "api-bom-list" %}',
            {
                part: partId,
                sub_part_detail: true,
                sub_part_trackable: buildInfo.tracked_parts,
            },
            {
                async: false,
                success: function(results) {
                    bom_items = results;
                }
            }
        );
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

    setupFilterList('builditems', $(table), options.filterTarget);

    var allocated_items = output == null ? null : output.allocations;

    function redrawAllocationData() {
        // Force a refresh of each row in the table
        // Note we cannot call 'refresh' because we are passing data from memory
        // var rows = $(table).bootstrapTable('getData');

        // How many rows are fully allocated?
        var allocated_rows = 0;

        bom_items.forEach(function(row) {
            $(table).bootstrapTable('updateByUniqueId', row.pk, row, true);

            if (isRowFullyAllocated(row)) {
                allocated_rows += 1;
            }
        });

        // Find the top-level progess bar for this build output
        var output_progress_bar = $(`#output-progress-${outputId}`);

        if (output_progress_bar.exists()) {
            if (bom_items.length > 0) {
                output_progress_bar.html(
                    makeProgressBar(
                        allocated_rows,
                        bom_items.length,
                        {
                            max_width: '150px',
                        }
                    )
                );
            }
        } else {
            console.warn(`Could not find progress bar for output '${outputId}'`);
        }
    }

    function reloadAllocationData(async=true) {
        // Reload stock allocation data for this particular build output

        inventreeGet(
            '{% url "api-build-item-list" %}',
            {
                build: buildId,
                part_detail: true,
                location_detail: true,
                output: output == null ? null : output.pk,
            },
            {
                async: async,
                success: function(response) {
                    allocated_items = response;

                    redrawAllocationData();

                }
            }
        );
    }

    if (allocated_items == null) {
        // No allocation data provided? Request from server (blocking)
        reloadAllocationData(false);
    } else {
        redrawAllocationData();
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
        // Prevent weird rounding issues
        row.required = formatDecimal(quantity, 15);
        return row.required;
    }

    function availableQuantity(row) {
        // Return the total available stock for a given row

        // Base stock
        var available = row.available_stock;

        // Substitute stock
        available += (row.available_substitute_stock || 0);

        // Variant stock
        if (row.allow_variants) {
            available += (row.available_variant_stock || 0);
        }

        return available;
    }

    function allocatedQuantity(row) {
        row.allocated = sumAllocationsForBomRow(row, allocated_items);
        return row.allocated;
    }

    function isRowFullyAllocated(row) {
        return allocatedQuantity(row) >= requiredQuantity(row);
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
                console.warn('getRowByUniqueId returned null');
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
                        // $(table).bootstrapTable('refresh');
                        reloadAllocationData();
                    },
                    output: output == null ? null : output.pk,
                }
            );
        });

        // Callback for 'buy' button
        $(table).find('.button-buy').click(function() {

            var pk = $(this).attr('pk');

            inventreeGet(
                `/api/part/${pk}/`,
                {},
                {
                    success: function(part) {
                        orderParts(
                            [part],
                            {}
                        );
                    }
                }
            );
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
                quantity: requiredQuantity(row) - allocatedQuantity(row),
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
                onSuccess: function(response, opts) {
                    reloadAllocationData();
                }
            });
        });
    }

    // Load table of BOM items
    $(table).inventreeTable({
        data: bom_items,
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
        sortable: true,
        showColumns: false,
        detailView: true,
        detailFilter: function(index, row) {
            return allocatedQuantity(row) > 0;
        },
        detailFormatter: function(index, row, element) {
            // Contruct an 'inner table' which shows which stock items have been allocated

            var subTableId = `allocation-table-${row.pk}`;

            var html = `<div class='sub-table'><table class='table table-condensed table-striped' id='${subTableId}'></table></div>`;

            element.html(html);

            var subTable = $(`#${subTableId}`);

            subTable.bootstrapTable({
                data: getAllocationsForBomRow(row, allocated_items),
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
                    onSuccess: reloadAllocationData,
                });
            });

            subTable.find('.button-allocation-delete').click(function() {
                var pk = $(this).attr('pk');

                constructForm(`/api/build/item/${pk}/`, {
                    method: 'DELETE',
                    title: '{% trans "Remove Allocation" %}',
                    onSuccess: reloadAllocationData,
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
                field: 'available_stock',
                title: '{% trans "Available" %}',
                sortable: true,
                formatter: function(value, row) {

                    var url = `/part/${row.sub_part_detail.pk}/?display=part-stock`;

                    // Calculate total "available" (unallocated) quantity
                    var substitute_stock = row.available_substitute_stock || 0;
                    var variant_stock = row.allow_variants ? (row.available_variant_stock || 0) : 0;

                    var available_stock = availableQuantity(row);

                    var required = requiredQuantity(row);

                    var text = '';

                    if (available_stock > 0) {
                        text += `${available_stock}`;
                    }

                    if (available_stock < required) {
                        text += `<span class='fas fa-times-circle icon-red float-right' title='{% trans "Insufficient stock available" %}'></span>`;
                    } else {
                        text += `<span class='fas fa-check-circle icon-green float-right' title='{% trans "Sufficient stock available" %}'></span>`;
                    }

                    if (available_stock <= 0) {
                        text += `<span class='badge rounded-pill bg-danger'>{% trans "No Stock Available" %}</span>`;
                    } else {
                        var extra = '';
                        if ((substitute_stock > 0) && (variant_stock > 0)) {
                            extra = '{% trans "Includes variant and substitute stock" %}';
                        } else if (variant_stock > 0) {
                            extra = '{% trans "Includes variant stock" %}';
                        } else if (substitute_stock > 0) {
                            extra = '{% trans "Includes substitute stock" %}';
                        }

                        if (extra) {
                            text += `<span title='${extra}' class='fas fa-info-circle float-right icon-blue'></span>`;
                        }
                    }

                    return renderLink(text, url);
                },
                sorter: function(valA, valB, rowA, rowB) {

                    return availableQuantity(rowA) > availableQuantity(rowB) ? 1 : -1;
                },
            },
            {
                field: 'allocated',
                title: '{% trans "Allocated" %}',
                sortable: true,
                formatter: function(value, row) {
                    var allocated = allocatedQuantity(row);
                    var required = requiredQuantity(row);
                    return makeProgressBar(allocated, required);
                },
                sorter: function(valA, valB, rowA, rowB) {
                    // Custom sorting function for progress bars

                    var aA = allocatedQuantity(rowA);
                    var aB = allocatedQuantity(rowB);

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
                        return (qA > qB) ? 1 : -1;
                    }

                    if (progressA == progressB) return 0;

                    return (progressA > progressB) ? 1 : -1;
                }
            },
            {
                field: 'actions',
                title: '{% trans "Actions" %}',
                formatter: function(value, row) {
                    // Generate action buttons for this build output
                    var html = `<div class='btn-group float-right' role='group'>`;

                    if (allocatedQuantity(row) < requiredQuantity(row)) {
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
                            disabled: allocatedQuantity(row) == 0,
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
 *  - source_location: ID / PK of the top-level StockLocation to source stock from (or null)
 */
function allocateStockToBuild(build_id, part_id, bom_items, options={}) {

    if (bom_items.length == 0) {

        showAlertDialog(
            '{% trans "Select Parts" %}',
            '{% trans "You must select at least one part to allocate" %}',
        );

        return;
    }

    // ID of the associated "build output" (or null)
    var output_id = options.output || null;

    var auto_fill_filters = {};

    var source_location = options.source_location;

    if (output_id) {
        // Request information on the particular build output (stock item)
        inventreeGet(`/api/stock/${output_id}/`, {}, {
            success: function(output) {
                if (output.quantity == 1 && output.serial != null) {
                    auto_fill_filters.serial = output.serial;
                }
            },
            async: false,
        });
    }

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
        <tr id='items_${pk}' class='part-allocation-row'>
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

        // Ensure the quantity sent to the form field is correctly formatted
        remaining = formatDecimal(remaining, 15);

        // We only care about entries which are not yet fully allocated
        if (remaining > 0) {
            table_entries += renderBomItemRow(bom_item, remaining);
        }
    }

    if (table_entries.length == 0) {

        showAlertDialog(
            '{% trans "All Parts Allocated" %}',
            '{% trans "All selected parts have been fully allocated" %}',
        );

        return;
    }

    var html = ``;

    // Render a "source location" input
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

            // Add callback to "clear" button for take_from field
            addClearCallback(
                'take_from',
                take_from_field,
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
                            available: true,
                            part_detail: true,
                            location_detail: true,
                        },
                        model: 'stockitem',
                        required: true,
                        render_part_detail: true,
                        render_location_detail: true,
                        render_pk: false,
                        auto_fill: true,
                        auto_fill_filters: auto_fill_filters,
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

            // Add remove-row button callbacks
            $(options.modal).find('.button-row-remove').click(function() {
                var pk = $(this).attr('pk');

                $(options.modal).find(`#items_${pk}`).remove();
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
                            showApiError(xhr, opts.url);
                            break;
                        }
                    }
                }
            );
        },
    });
}


/**
 * Automatically allocate stock items to a build
 */
function autoAllocateStockToBuild(build_id, bom_items=[], options={}) {

    var html = `
    <div class='alert alert-block alert-info'>
    <strong>{% trans "Automatic Stock Allocation" %}</strong><br>
    {% trans "Stock items will be automatically allocated to this build order, according to the provided guidelines" %}:
    <ul>
        <li>{% trans "If a location is specifed, stock will only be allocated from that location" %}</li>
        <li>{% trans "If stock is considered interchangeable, it will be allocated from the first location it is found" %}</li>
        <li>{% trans "If substitute stock is allowed, it will be used where stock of the primary part cannot be found" %}</li>
    </ul>
    </div>
    `;

    var fields = {
        location: {
            value: options.location,
        },
        exclude_location: {},
        interchangeable: {
            value: true,
        },
        substitutes: {
            value: true,
        },
    };

    constructForm(`/api/build/${build_id}/auto-allocate/`, {
        method: 'POST',
        fields: fields,
        title: '{% trans "Allocate Stock Items" %}',
        confirm: true,
        preFormContent: html,
        onSuccess: function(response) {
            if (options.onSuccess) {
                options.onSuccess(response);
            }
        }
    });
}


/*
 * Display a table of Build orders
 */
function loadBuildTable(table, options) {

    // Ensure the table starts in a known state
    $(table).bootstrapTable('destroy');

    var params = options.params || {};

    var filters = {};

    params['part_detail'] = true;

    if (!options.disableFilters) {
        filters = loadTableFilters('build');
    }

    for (var key in params) {
        filters[key] = params[key];
    }

    var filterTarget = options.filterTarget || null;

    setupFilterList('build', table, filterTarget, {download: true});

    // Which display mode to use for the build table?
    var display_mode = inventreeLoad('build-table-display-mode', 'list');
    var tree_enable = display_mode == 'tree';

    var loaded_calendar = false;

    // Function for rendering BuildOrder calendar display
    function buildEvents(calendar) {
        var start = startDate(calendar);
        var end = endDate(calendar);

        clearEvents(calendar);

        // Extract current filters from table
        var table_options = $(table).bootstrapTable('getOptions');
        var filters = table_options.query_params || {};

        filters.min_date = start;
        filters.max_date = end;
        filters.part_detail = true;

        // Request build orders from the server within specified date range
        inventreeGet(
            '{% url "api-build-list" %}',
            filters,
            {
                success: function(response) {
                    var prefix = global_settings.BUILDORDER_REFERENCE_PREFIX;

                    for (var idx = 0; idx < response.length; idx++) {

                        var order = response[idx];

                        var date = order.creation_date;

                        if (order.completion_date) {
                            date = order.completion_date;
                        } else if (order.target_date) {
                            date = order.target_date;
                        }

                        var title = `${prefix}${order.reference}`;

                        var color = '#4c68f5';

                        if (order.completed) {
                            color = '#25c234';
                        } else if (order.overdue) {
                            color = '#c22525';
                        }

                        var event = {
                            title: title,
                            start: date,
                            end: date,
                            url: `/build/${order.pk}/`,
                            backgroundColor: color,
                        };

                        calendar.addEvent(event);
                    }
                }
            }
        );
    }

    $(table).inventreeTable({
        method: 'get',
        formatNoMatches: function() {
            return '{% trans "No builds matching query" %}';
        },
        url: '{% url "api-build-list" %}',
        queryParams: filters,
        groupBy: false,
        sidePagination: 'server',
        name: 'builds',
        original: params,
        treeEnable: tree_enable,
        uniqueId: 'pk',
        rootParentId: options.parentBuild || null,
        idField: 'pk',
        parentIdField: 'parent',
        treeShowField: tree_enable ? 'reference' : null,
        showColumns: display_mode == 'list' || display_mode == 'tree',
        showCustomView: display_mode == 'calendar',
        showCustomViewButton: false,
        disablePagination: display_mode == 'calendar',
        search: display_mode != 'calendar',
        buttons: constructOrderTableButtons({
            prefix: 'build',
            callback: function() {
                // Force complete reload of the table
                loadBuildTable(table, options);
            }
        }),
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
                field: 'completed',
                title: '{% trans "Progress" %}',
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
                formatter: function(value) {
                    return renderDate(value);
                }
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
                        return '-';
                    }
                }
            },
            {
                field: 'target_date',
                title: '{% trans "Target Date" %}',
                sortable: true,
                formatter: function(value) {
                    return renderDate(value);
                }
            },
            {
                field: 'completion_date',
                title: '{% trans "Completion Date" %}',
                sortable: true,
                formatter: function(value) {
                    return renderDate(value);
                }
            },
        ],
        customView: function(data) {
            return `<div id='build-order-calendar'></div>`;
        },
        onRefresh: function() {
            loadBuildTable(table, options);
        },
        onLoadSuccess: function() {

            if (tree_enable) {
                $(table).treegrid({
                    treeColumn: 1,
                });

                table.treegrid('expandAll');
            } else if (display_mode == 'calendar') {

                if (!loaded_calendar) {
                    loaded_calendar = true;

                    var el = document.getElementById('build-order-calendar');

                    calendar = new FullCalendar.Calendar(el, {
                        initialView: 'dayGridMonth',
                        nowIndicator: true,
                        aspectRatio: 2.5,
                        locale: options.locale,
                        datesSet: function() {
                            buildEvents(calendar);
                        }
                    });

                    calendar.render();
                } else {
                    calendar.render();
                }
            }
        }
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
