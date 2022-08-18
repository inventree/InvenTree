{% load i18n %}

/* globals
    constructForm,
    exportFormatOptions,
    imageHoverIcon,
    inventreeGet,
    inventreePut,
    launchModalForm,
    loadTableFilters,
    makePartIcons,
    renderLink,
    setupFilterList,
    yesNoLabel,
*/

/* exported
    constructBomUploadTable,
    deleteBomItems,
    downloadBomTemplate,
    exportBom,
    newPartFromBomWizard,
    loadBomTable,
    loadUsedInTable,
    removeRowFromBomWizard,
    removeColFromBomWizard,
    submitBomTable
*/


/* Construct a table of data extracted from a BOM file.
 * This data is used to import a BOM interactively.
 */
function constructBomUploadTable(data, options={}) {

    if (!data.rows) {
        // TODO: Error message!
        return;
    }

    function constructRow(row, idx, fields) {
        // Construct an individual row from the provided data

        var field_options = {
            hideLabels: true,
            hideClearButton: true,
            form_classes: 'bom-form-group',
        };

        function constructRowField(field_name) {

            var field = fields[field_name] || null;

            if (!field) {
                return `Cannot render field '${field_name}`;
            }

            field.value = row.data[field_name];

            return constructField(`items_${field_name}_${idx}`, field, field_options);

        }

        // Construct form inputs
        var sub_part = constructRowField('sub_part');
        var quantity = constructRowField('quantity');
        var reference = constructRowField('reference');
        var overage = constructRowField('overage');
        var variants = constructRowField('allow_variants');
        var inherited = constructRowField('inherited');
        var optional = constructRowField('optional');
        var note = constructRowField('note');

        var buttons = `<div class='btn-group float-right' role='group'>`;

        buttons += makeIconButton('fa-info-circle', 'button-row-data', idx, '{% trans "Display row data" %}');
        buttons += makeIconButton('fa-times icon-red', 'button-row-remove', idx, '{% trans "Remove row" %}');

        buttons += `</div>`;

        var html = `
        <tr id='items_${idx}' class='bom-import-row' idx='${idx}'>
            <td id='col_sub_part_${idx}'>${sub_part}</td>
            <td id='col_quantity_${idx}'>${quantity}</td>
            <td id='col_reference_${idx}'>${reference}</td>
            <td id='col_overage_${idx}'>${overage}</td>
            <td id='col_variants_${idx}'>${variants}</td>
            <td id='col_inherited_${idx}'>${inherited}</td>
            <td id='col_optional_${idx}'>${optional}</td>
            <td id='col_note_${idx}'>${note}</td>
            <td id='col_buttons_${idx}'>${buttons}</td>
        </tr>`;

        $('#bom-import-table tbody').append(html);

        // Handle any errors raised by initial data import
        if (row.data.errors.part) {
            addFieldErrorMessage(`items_sub_part_${idx}`, row.data.errors.part);
        }

        if (row.data.errors.quantity) {
            addFieldErrorMessage(`items_quantity_${idx}`, row.data.errors.quantity);
        }

        // Initialize the "part" selector for this row
        initializeRelatedField(
            {
                name: `items_sub_part_${idx}`,
                value: row.data.part,
                api_url: '{% url "api-part-list" %}',
                filters: {
                    component: true,
                },
                model: 'part',
                required: true,
                auto_fill: false,
                onSelect: function(data, field, opts) {
                    // TODO?
                },
            }
        );

        // Add callback for "remove row" button
        $(`#button-row-remove-${idx}`).click(function() {
            $(`#items_${idx}`).remove();
        });

        // Add callback for "show data" button
        $(`#button-row-data-${idx}`).click(function() {

            var modal = createNewModal({
                title: '{% trans "Row Data" %}',
                closeText: '{% trans "Close" %}',
                hideSubmitButton: true
            });

            // Prettify the original import data
            var pretty = JSON.stringify(
                {
                    columns: data.columns,
                    row: row.original,
                }, undefined, 4
            );

            var html = `
            <div class='alert alert-block'>
            <pre><code>${pretty}</code></pre>
            </div>`;

            modalSetContent(modal, html);

            $(modal).modal('show');

        });
    }

    // Request API endpoint options
    getApiEndpointOptions('{% url "api-bom-list" %}', function(response) {

        var fields = response.actions.POST;

        data.rows.forEach(function(row, idx) {
            constructRow(row, idx, fields);
        });
    });
}


/* Extract rows from the BOM upload table,
 * and submit data to the server
 */
function submitBomTable(part_id, options={}) {

    // Extract rows from the form
    var rows = [];

    var idx_values = [];

    var url = '{% url "api-bom-import-submit" %}';

    $('.bom-import-row').each(function() {
        var idx = $(this).attr('idx');

        idx_values.push(idx);

        // Extract each field from the row
        rows.push({
            part: part_id,
            sub_part: getFormFieldValue(`items_sub_part_${idx}`, {}),
            quantity: getFormFieldValue(`items_quantity_${idx}`, {}),
            reference: getFormFieldValue(`items_reference_${idx}`, {}),
            overage: getFormFieldValue(`items_overage_${idx}`, {}),
            allow_variants: getFormFieldValue(`items_allow_variants_${idx}`, {type: 'boolean'}),
            inherited: getFormFieldValue(`items_inherited_${idx}`, {type: 'boolean'}),
            optional: getFormFieldValue(`items_optional_${idx}`, {type: 'boolean'}),
            note: getFormFieldValue(`items_note_${idx}`, {}),
        });
    });

    var data = {
        items: rows,
    };

    var options = {
        nested: {
            items: idx_values,
        }
    };

    getApiEndpointOptions(url, function(response) {
        var fields = response.actions.POST;

        // Disable the "Submit BOM" button
        $('#bom-submit').prop('disabled', true);
        $('#bom-submit-icon').show();

        inventreePut(url, data, {
            method: 'POST',
            success: function(response) {
                window.location.href = `/part/${part_id}/?display=bom`;
            },
            error: function(xhr) {
                switch (xhr.status) {
                case 400:
                    handleFormErrors(xhr.responseJSON, fields, options);
                    break;
                default:
                    showApiError(xhr, url);
                    break;
                }

                // Re-enable the submit button
                $('#bom-submit').prop('disabled', false);
                $('#bom-submit-icon').hide();
            }
        });
    });
}


function downloadBomTemplate(options={}) {

    var format = options.format;

    if (!format) {
        format = inventreeLoad('bom-export-format', 'csv');
    }

    constructFormBody({}, {
        title: '{% trans "Download BOM Template" %}',
        fields: {
            format: {
                label: '{% trans "Format" %}',
                help_text: '{% trans "Select file format" %}',
                required: true,
                type: 'choice',
                value: format,
                choices: exportFormatOptions(),
            }
        },
        onSubmit: function(fields, opts) {
            var format = getFormFieldValue('format', fields['format'], opts);

            // Save the format for next time
            inventreeSave('bom-export-format', format);

            // Hide the modal
            $(opts.modal).modal('hide');

            // Download the file
            location.href = `{% url "bom-upload-template" %}?format=${format}`;

        }
    });
}


/**
 * Export BOM (Bill of Materials) for the specified Part instance
 */
function exportBom(part_id, options={}) {

    constructFormBody({}, {
        title: '{% trans "Export BOM" %}',
        fields: {
            format: {
                label: '{% trans "Format" %}',
                help_text: '{% trans "Select file format" %}',
                required: true,
                type: 'choice',
                value: inventreeLoad('bom-export-format', 'csv'),
                choices: exportFormatOptions(),
            },
            cascade: {
                label: '{% trans "Multi Level BOM" %}',
                help_text: '{% trans "Include BOM data for subassemblies" %}',
                type: 'boolean',
                value: inventreeLoad('bom-export-cascading', true),
            },
            levels: {
                label: '{% trans "Levels" %}',
                help_text: '{% trans "Select maximum number of BOM levels to export (0 = all levels)" %}',
                type: 'integer',
                value: 0,
                required: true,
                min_value: 0,
            },
            parameter_data: {
                label: '{% trans "Include Parameter Data" %}',
                help_text: '{% trans "Include part  parameter data in exported BOM" %}',
                type: 'boolean',
                value: inventreeLoad('bom-export-parameter_data', false),
            },
            stock_data: {
                label: '{% trans "Include Stock Data" %}',
                help_text: '{% trans "Include part stock data in exported BOM" %}',
                type: 'boolean',
                value: inventreeLoad('bom-export-stock_data', false),
            },
            manufacturer_data: {
                label: '{% trans "Include Manufacturer Data" %}',
                help_text: '{% trans "Include part manufacturer data in exported BOM" %}',
                type: 'boolean',
                value: inventreeLoad('bom-export-manufacturer_data', false),
            },
            supplier_data: {
                label: '{% trans "Include Supplier Data" %}',
                help_text: '{% trans "Include part supplier data in exported BOM" %}',
                type: 'boolean',
                value: inventreeLoad('bom-export-supplier_data', false),
            }
        },
        onSubmit: function(fields, opts) {

            // Extract values from the form
            var field_names = ['format', 'cascade', 'levels', 'parameter_data', 'stock_data', 'manufacturer_data', 'supplier_data'];

            var url = `/part/${part_id}/bom-download/?`;

            field_names.forEach(function(fn) {
                var val = getFormFieldValue(fn, fields[fn], opts);

                // Update user preferences
                inventreeSave(`bom-export-${fn}`, val);

                url += `${fn}=${val}&`;
            });

            $(opts.modal).modal('hide');

            // Redirect to the BOM file download
            location.href = url;
        }
    });

}


function bomItemFields() {

    return {
        part: {
            hidden: true,
        },
        sub_part: {
            secondary: {
                title: '{% trans "New Part" %}',
                fields: function() {
                    var fields = partFields();

                    // Set to a "component" part
                    fields.component.value = true;

                    return fields;
                },
                groups: partGroups(),
            }
        },
        quantity: {},
        reference: {},
        overage: {},
        note: {},
        allow_variants: {},
        inherited: {},
        optional: {},
    };

}


function reloadBomTable(table) {

    table.bootstrapTable('refresh');
}


function removeRowFromBomWizard(e) {
    /* Remove a row from BOM upload wizard
     */

    e = e || window.event;

    var src = e.target || e.srcElement;

    var table = $(src).closest('table');

    // Which column was clicked?
    var row = $(src).closest('tr');

    row.remove();

    var rowNum = 1;
    var colNum = 0;

    table.find('tr').each(function() {

        colNum++;

        if (colNum >= 3) {
            var cell = $(this).find('td:eq(1)');
            cell.text(rowNum++);
        }
    });
}


function removeColFromBomWizard(e) {
    /* Remove a column from BOM upload wizard
     */

    e = e || window.event;

    var src = e.target || e.srcElement;

    // Which column was clicked?
    var col = $(src).closest('th').index();

    var table = $(src).closest('table');

    table.find('tr').each(function() {
        this.removeChild(this.cells[col]);
    });
}


function newPartFromBomWizard(e) {
    /* Create a new part directly from the BOM wizard.
     */

    e = e || window.event;

    var src = e.target || e.srcElement;

    var row = $(src).closest('tr');

    launchModalForm('/part/new/', {
        data: {
            'description': row.attr('part-description'),
            'name': row.attr('part-name'),
        },
        success: function(response) {
            /* A new part has been created! Push it as an option.
             */

            var select = row.attr('part-select');

            var option = new Option(response.text, response.pk, true, true);
            $(select).append(option).trigger('change');
        }
    });
}


/*
 * Launch a modal dialog displaying the "substitute parts" for a particular BomItem
 *
 * If editable, allows substitutes to be added and deleted
 */
function bomSubstitutesDialog(bom_item_id, substitutes, options={}) {

    // Reload data for the parent table
    function reloadParentTable() {
        if (options.table) {
            options.table.bootstrapTable('refresh');
        }
    }

    // Extract a list of all existing "substitute" id values
    function getSubstituteIdValues(modal) {

        var id_values = [];

        $(modal).find('.substitute-row').each(function(el) {
            var part = $(this).attr('part');
            id_values.push(part);
        });

        return id_values;
    }

    function renderSubstituteRow(substitute) {

        var pk = substitute.pk;

        var part = substitute.part_detail;

        var thumb = thumbnailImage(part.thumbnail || part.image);

        var buttons = '';

        buttons += makeIconButton('fa-times icon-red', 'button-row-remove', pk, '{% trans "Remove substitute part" %}');

        // Render a single row
        var html = `
        <tr id='substitute-row-${pk}' class='substitute-row' part='${substitute.part}'>
            <td id='part-${pk}'>
                <a href='/part/${part.pk}/'>
                    ${thumb} ${part.full_name}
                </a>
            </td>
            <td id='description-${pk}'><em>${part.description}</em></td>
            <td>${buttons}</td>
        </tr>
        `;

        return html;
    }

    // Construct a table to render the rows
    var rows = '';

    substitutes.forEach(function(sub) {
        rows += renderSubstituteRow(sub);
    });

    var part_thumb = thumbnailImage(options.sub_part_detail.thumbnail || options.sub_part_detail.image);
    var part_name = options.sub_part_detail.full_name;
    var part_desc = options.sub_part_detail.description;

    var html = `
    <div class='alert alert-block'>
    <strong>{% trans "Base Part" %}</strong><hr>
    ${part_thumb} ${part_name} - <em>${part_desc}</em>
    </div>
    `;

    // Add a table of individual rows
    html += `
    <table class='table table-striped table-condensed' id='substitute-table'>
        <thead>
            <tr>
                <th>{% trans "Part" %}</th>
                <th>{% trans "Description" %}</th>
                <th><!-- Actions --></th>
            </tr>
        </thead>
        <tbody>
            ${rows}
        </tbody>
    </table>
    `;

    html += `
    <div class='alert alert-success alert-block'>
        {% trans "Select and add a new substitute part using the input below" %}
    </div>
    `;

    // Add a callback to remove a row from the table
    function addRemoveCallback(modal, element) {
        $(modal).find(element).click(function() {
            var pk = $(this).attr('pk');

            var pre = `
            <div class='alert alert-block alert-warning'>
            {% trans "Are you sure you wish to remove this substitute part link?" %}
            </div>
            `;

            constructForm(`/api/bom/substitute/${pk}/`, {
                method: 'DELETE',
                title: '{% trans "Remove Substitute Part" %}',
                preFormContent: pre,
                confirm: true,
                onSuccess: function() {
                    $(modal).find(`#substitute-row-${pk}`).remove();
                    reloadParentTable();
                }
            });
        });
    }

    constructForm('{% url "api-bom-substitute-list" %}', {
        method: 'POST',
        fields: {
            bom_item: {
                hidden: true,
                value: bom_item_id,
            },
            part: {
                required: false,
                adjustFilters: function(query, opts) {

                    var subs = getSubstituteIdValues(opts.modal);

                    // Also exclude the "master" part (if provided)
                    if (options.sub_part) {
                        subs.push(options.sub_part);
                    }

                    if (subs.length > 0) {
                        query.exclude_id = subs;
                    }

                    return query;
                }
            },
        },
        preFormContent: html,
        closeText: '{% trans "Close" %}',
        submitText: '{% trans "Add Substitute" %}',
        title: '{% trans "Edit BOM Item Substitutes" %}',
        afterRender: function(fields, opts) {
            addRemoveCallback(opts.modal, '.button-row-remove');
        },
        preventClose: true,
        onSuccess: function(response, opts) {

            // Clear the form
            var field = {
                type: 'related field',
            };

            updateFieldValue('part', null, field, opts);

            // Add the new substitute to the table
            var row = renderSubstituteRow(response);
            $(opts.modal).find('#substitute-table > tbody:last-child').append(row);

            // Add a callback to the new button
            addRemoveCallback(opts.modal, `#button-row-remove-${response.pk}`);

            // Re-enable the "submit" button
            enableSubmitButton(opts, true);

            // Reload the parent BOM table
            reloadParentTable();
        }
    });
}


/*
 * Delete the selected BOM items from the database
 */
function deleteBomItems(items, options={}) {

    function renderItem(item, opts={}) {

        var sub_part = item.sub_part_detail;
        var thumb = thumbnailImage(sub_part.thumbnail || sub_part.image);

        var html = `
        <tr>
            <td>${thumb} ${sub_part.full_name}</td>
            <td>${item.reference}</td>
            <td>${item.quantity}
        </tr>
        `;

        return html;
    }

    var rows = '';
    var ids = [];

    items.forEach(function(item) {
        rows += renderItem(item);
        ids.push(item.pk);
    });

    var html = `
    <div class='alert alert-block alert-danger'>
    {% trans "All selected BOM items will be deleted" %}
    </div>

    <table class='table table-striped table-condensed'>
        <tr>
            <th>{% trans "Part" %}</th>
            <th>{% trans "Reference" %}</th>
            <th>{% trans "Quantity" %}</th>
        </tr>
        ${rows}
    </table>
    `;

    constructForm('{% url "api-bom-list"  %}', {
        method: 'DELETE',
        multi_delete: true,
        title: '{% trans "Delete selected BOM items?" %}',
        form_data: {
            items: ids,
        },
        preFormContent: html,
        onSuccess: options.success,
    });
}


function loadBomTable(table, options={}) {
    /* Load a BOM table with some configurable options.
     *
     * Following options are available:
     * editable      - Should the BOM table be editable?
     * bom_url       - Address to request BOM data from
     * part_url      - Address to request Part data from
     * parent_id     - Parent ID of the owning part
     *
     * BOM data are retrieved from the server via AJAX query
     */

    var params = {
        part: options.parent_id,
        ordering: 'name',
    };

    // Do we show part pricing in the BOM table?
    var show_pricing = global_settings.PART_SHOW_PRICE_IN_BOM;

    params.include_pricing = show_pricing == true;

    if (options.part_detail) {
        params.part_detail = true;
    }

    params.sub_part_detail = true;

    var filters = {};

    if (!options.disableFilters) {
        filters = loadTableFilters('bom');
    }

    for (var key in params) {
        filters[key] = params[key];
    }

    setupFilterList('bom', $(table));

    function availableQuantity(row) {

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

    // Construct the table columns
    var cols = [];

    if (options.editable) {
        cols.push({
            field: 'ID',
            title: '',
            checkbox: true,
            visible: true,
            switchable: false,
            formatter: function(value, row) {
                // Disable checkbox if the row is defined for a *different* part!
                if (row.part != options.parent_id) {
                    return {
                        disabled: true,
                    };
                } else {
                    return value;
                }
            }
        });
    }

    // Set the parent ID of the multi-level table.
    // We prepend this with the literal string value 'top-level-',
    // because otherwise the unfortunate situation where BomItem.pk == BomItem.part.pk
    // AND THIS BREAKS EVERYTHING
    var parent_id = `top-level-${options.parent_id}`;

    // Part column
    cols.push(
        {
            field: 'sub_part_detail.full_name',
            title: '{% trans "Part" %}',
            sortable: true,
            switchable: false,
            formatter: function(value, row) {
                var url = `/part/${row.sub_part}/`;
                var html = '';

                var sub_part = row.sub_part_detail;

                // Display an extra icon if this part is an assembly
                if (sub_part.assembly) {

                    if (row.sub_assembly_received) {
                        // Data received, ignore
                    } else if (row.sub_assembly_requested) {
                        html += `<a href='#'><span class='fas fa-sync fa-spin'></span></a>`;
                    } else {
                        html += `
                            <a href='#' pk='${row.pk}' class='load-sub-assembly' id='load-sub-assembly-${row.pk}'>
                                <span class='fas fa-sync-alt' title='{% trans "Load BOM for subassembly" %}'></span>
                            </a> `;
                    }
                }

                html += imageHoverIcon(sub_part.thumbnail) + renderLink(row.sub_part_detail.full_name, url);

                html += makePartIcons(sub_part);

                if (row.substitutes && row.substitutes.length > 0) {
                    html += makeIconBadge('fa-exchange-alt', '{% trans "Substitutes Available" %}');
                }

                if (row.allow_variants) {
                    html += makeIconBadge('fa-sitemap', '{% trans "Variant stock allowed" %}');
                }

                return html;
            }
        }
    );


    // Part description
    cols.push(
        {
            field: 'sub_part_detail.description',
            title: '{% trans "Description" %}',
        }
    );

    // Part reference
    cols.push({
        field: 'reference',
        title: '{% trans "Reference" %}',
        searchable: true,
        sortable: true,
    });

    // Part quantity
    cols.push({
        field: 'quantity',
        title: '{% trans "Quantity" %}',
        searchable: false,
        sortable: true,
        formatter: function(value, row) {
            var text = value;

            // The 'value' is a text string with (potentially) multiple trailing zeros
            // Let's make it a bit more pretty
            text = parseFloat(text);

            if (row.optional) {
                text += ' ({% trans "Optional" %})';
            }

            if (row.overage) {
                text += `<small> (${row.overage})    </small>`;
            }

            return text;
        },
        footerFormatter: function(data) {

            // Top-level BOM count
            var top_total = 0;

            // Total BOM count
            var all_total = 0;

            data.forEach(function(row) {
                var q = +row['quantity'] || 0;

                all_total += q;

                if (row.part == options.parent_id) {
                    top_total += q;
                }
            });

            var total = `${top_total}`;

            if (top_total != all_total) {
                total += ` / ${all_total}`;
            }

            return total;
        }
    });

    cols.push({
        field: 'available_stock',
        title: '{% trans "Available" %}',
        searchable: false,
        sortable: true,
        formatter: function(value, row) {

            var url = `/part/${row.sub_part_detail.pk}/?display=part-stock`;

            // Calculate total "available" (unallocated) quantity
            var substitute_stock = row.available_substitute_stock || 0;
            var variant_stock = row.allow_variants ? (row.available_variant_stock || 0) : 0;

            var available_stock = availableQuantity(row);

            var text = `${available_stock}`;

            if (available_stock <= 0) {
                text += `<span class='fas fa-times-circle icon-red float-right' title='{% trans "No Stock Available" %}'></span>`;
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

            if (row.on_order && row.on_order > 0) {
                text += `<span class='fas fa-shopping-cart float-right' title='{% trans "On Order" %}: ${row.on_order}'></span>`;
            }

            return renderLink(text, url);
        }
    });

    cols.push({
        field: 'substitutes',
        title: '{% trans "Substitutes" %}',
        searchable: false,
        sortable: true,
        formatter: function(value, row) {
            if (row.substitutes && row.substitutes.length > 0) {
                return row.substitutes.length;
            } else {
                return `-`;
            }
        }
    });

    if (show_pricing) {
        cols.push({
            field: 'purchase_price_range',
            title: '{% trans "Purchase Price Range" %}',
            searchable: false,
            sortable: true,
        });

        cols.push({
            field: 'purchase_price_avg',
            title: '{% trans "Purchase Price Average" %}',
            searchable: false,
            sortable: true,
        });

        cols.push({
            field: 'price_range',
            title: '{% trans "Supplier Cost" %}',
            sortable: true,
            formatter: function(value) {
                if (value) {
                    return value;
                } else {
                    return `<span class='warning-msg'>{% trans 'No supplier pricing available' %}</span>`;
                }
            }
        });
    }

    cols.push({
        field: 'optional',
        title: '{% trans "Optional" %}',
        searchable: false,
        formatter: function(value) {
            return yesNoLabel(value);
        }
    });

    cols.push({
        field: 'allow_variants',
        title: '{% trans "Allow Variants" %}',
        formatter: function(value) {
            return yesNoLabel(value);
        }
    });

    cols.push({
        field: 'inherited',
        title: '{% trans "Inherited" %}',
        searchable: false,
        formatter: function(value, row) {
            // This BOM item *is* inheritable, but is defined for this BOM
            if (!row.inherited) {
                return yesNoLabel(false);
            } else if (row.part == options.parent_id) {
                return yesNoLabel(true);
            } else {
                // If this BOM item is inherited from a parent part
                return renderLink(
                    '{% trans "View BOM" %}',
                    `/part/${row.part}/bom/`,
                );
            }
        }
    });

    cols.push(
        {
            field: 'can_build',
            title: '{% trans "Can Build" %}',
            formatter: function(value, row) {
                var can_build = 0;

                var available = availableQuantity(row);

                if (row.quantity > 0) {
                    can_build = available / row.quantity;
                }

                var text = formatDecimal(can_build, 2);

                // Take "on order" quantity into account
                if (row.on_order && row.on_order > 0 && row.quantity > 0) {
                    available += row.on_order;
                    can_build = available / row.quantity;

                    text += `<span class='fas fa-info-circle icon-blue float-right' title='{% trans "Including On Order" %}: ${can_build}'></span>`;
                }

                return text;
            },
            footerFormatter: function(data) {
                var can_build = null;

                data.forEach(function(row) {
                    if (row.part == options.parent_id && row.quantity > 0) {
                        var cb = availableQuantity(row) / row.quantity;

                        if (can_build == null || cb < can_build) {
                            can_build = cb;
                        }
                    }
                });

                if (can_build == null) {
                    can_build = '-';
                }

                return can_build;
            },
            sorter: function(valA, valB, rowA, rowB) {
                // Function to sort the "can build" quantity
                var cb_a = 0;
                var cb_b = 0;

                if (rowA.quantity > 0) {
                    cb_a = availableQuantity(rowA) / rowA.quantity;
                }

                if (rowB.quantity > 0) {
                    cb_b = availableQuantity(rowB) / rowB.quantity;
                }

                return (cb_a > cb_b) ? 1 : -1;
            },
            sortable: true,
        }
    );

    // Part notes
    cols.push(
        {
            field: 'note',
            title: '{% trans "Notes" %}',
            searchable: true,
            sortable: true,
        }
    );

    if (options.editable) {

        cols.push({
            title: '{% trans "Actions" %}',
            switchable: false,
            field: 'pk',
            visible: true,
            formatter: function(value, row) {

                if (row.part == options.parent_id) {

                    var bValidate = makeIconButton('fa-check-circle icon-green', 'bom-validate-button', row.pk, '{% trans "Validate BOM Item" %}');

                    var bValid = makeIconButton('fa-check-double icon-green', 'bom-valid-button', row.pk, '{% trans "This line has been validated" %}', {disabled: true});

                    var bSubs = makeIconButton('fa-exchange-alt icon-blue', 'bom-substitutes-button', row.pk, '{% trans "Edit substitute parts" %}');

                    var bEdit = makeIconButton('fa-edit icon-blue', 'bom-edit-button', row.pk, '{% trans "Edit BOM Item" %}');

                    var bDelt = makeIconButton('fa-trash-alt icon-red', 'bom-delete-button', row.pk, '{% trans "Delete BOM Item" %}');

                    var html = `<div class='btn-group float-right' role='group' style='min-width: 100px;'>`;

                    if (!row.validated) {
                        html += bValidate;
                    } else {
                        html += bValid;
                    }

                    html += bEdit;
                    html += bSubs;
                    html += bDelt;

                    html += `</div>`;

                    return html;
                } else {
                    // Return a link to the external BOM

                    return renderLink(
                        '{% trans "View BOM" %}',
                        `/part/${row.part}/bom/`
                    );
                }
            }
        });
    }

    // Function to request BOM data for sub-items
    // This function may be called recursively for multi-level BOMs
    function requestSubItems(bom_pk, part_pk, depth=0) {

        inventreeGet(
            options.bom_url,
            {
                part: part_pk,
                sub_part_detail: true,
                include_pricing: show_pricing == true,
            },
            {
                success: function(response) {

                    // Add the returned sub-items to the table
                    for (var idx = 0; idx < response.length; idx++) {
                        response[idx].parentId = bom_pk;
                    }

                    var row = $(table).bootstrapTable('getRowByUniqueId', bom_pk);
                    row.sub_assembly_received = true;

                    $(table).bootstrapTable('updateByUniqueId', bom_pk, row, true);

                    table.bootstrapTable('append', response);
                },
                error: function(xhr) {
                    console.error('Error requesting BOM for part=' + part_pk);
                    showApiError(xhr);
                }
            }
        );
    }

    table.inventreeTable({
        treeEnable: true,
        rootParentId: parent_id,
        idField: 'pk',
        uniqueId: 'pk',
        parentIdField: 'parentId',
        treeShowField: 'sub_part',
        showColumns: true,
        showFooter: true,
        name: 'bom',
        sortable: true,
        search: true,
        rowStyle: function(row) {

            var classes = [];

            // Shade rows differently if they are for different parent parts
            if (row.part != options.parent_id) {
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
        queryParams: filters,
        original: params,
        columns: cols,
        url: options.bom_url,
        onPostBody: function() {

            table.treegrid({
                treeColumn: 1,
                onExpand: function() {
                }
            });

            table.treegrid('collapseAll');

            // Callback for 'load sub assembly' button
            $(table).find('.load-sub-assembly').click(function(event) {

                event.preventDefault();

                var pk = $(this).attr('pk');
                var row = $(table).bootstrapTable('getRowByUniqueId', pk);

                // Request BOM data for this subassembly
                requestSubItems(row.pk, row.sub_part);

                row.sub_assembly_requested = true;
                $(table).bootstrapTable('updateByUniqueId', pk, row, true);
            });
        },
        onLoadSuccess: function() {
            if (options.editable) {
                table.bootstrapTable('uncheckAll');
            }
        },
    });

    // In editing mode, attached editables to the appropriate table elements
    if (options.editable) {

        // Callback for "delete" button
        table.on('click', '.bom-delete-button', function() {

            var pk = $(this).attr('pk');

            var item = table.bootstrapTable('getRowByUniqueId', pk);

            deleteBomItems([item], {
                success: function() {
                    reloadBomTable(table);
                }
            });
        });

        // Callback for "edit" button
        table.on('click', '.bom-edit-button', function() {

            var pk = $(this).attr('pk');

            var fields = bomItemFields();

            constructForm(`/api/bom/${pk}/`, {
                fields: fields,
                title: '{% trans "Edit BOM Item" %}',
                focus: 'sub_part',
                onSuccess: function() {
                    reloadBomTable(table);
                }
            });
        });

        // Callback for "validate" button
        table.on('click', '.bom-validate-button', function() {

            var pk = $(this).attr('pk');
            var url = `/api/bom/${pk}/validate/`;

            inventreePut(
                url,
                {
                    valid: true
                },
                {
                    method: 'PATCH',
                    success: function() {
                        reloadBomTable(table);
                    }
                }
            );
        });

        // Callback for "substitutes" button
        table.on('click', '.bom-substitutes-button', function() {
            var pk = $(this).attr('pk');

            var row = table.bootstrapTable('getRowByUniqueId', pk);
            var subs = row.substitutes || [];

            bomSubstitutesDialog(
                pk,
                subs,
                {
                    table: table,
                    part: row.part,
                    sub_part: row.sub_part,
                    sub_part_detail: row.sub_part_detail,
                }
            );
        });
    }
}


/*
 * Load a table which shows the assemblies which "require" a certain part.
 *
 * Arguments:
 * - table: The ID string of the table element e.g. '#used-in-table'
 * - part_id: The ID (PK) of the part we are interested in
 *
 * Options:
 * -
 *
 * The following "options" are available.
 */
function loadUsedInTable(table, part_id, options={}) {

    var params = options.params || {};

    params.uses = part_id;
    params.part_detail = true;
    params.sub_part_detail = true,
    params.show_pricing = global_settings.PART_SHOW_PRICE_IN_BOM;

    var filters = {};

    if (!options.disableFilters) {
        filters = loadTableFilters('usedin');
    }

    for (var key in params) {
        filters[key] = params[key];
    }

    setupFilterList('usedin', $(table), options.filterTarget || '#filter-list-usedin');

    function loadVariantData(row) {
        // Load variants information for inherited BOM rows

        inventreeGet(
            '{% url "api-part-list" %}',
            {
                assembly: true,
                ancestor: row.part,
            },
            {
                success: function(variantData) {
                    // Iterate through each variant item
                    for (var jj = 0; jj < variantData.length; jj++) {
                        variantData[jj].parent = row.pk;

                        var variant = variantData[jj];

                        // Add this variant to the table, augmented
                        $(table).bootstrapTable('append', [{
                            // Point the parent to the "master" assembly row
                            parent: row.pk,
                            part: variant.pk,
                            part_detail: variant,
                            sub_part: row.sub_part,
                            sub_part_detail: row.sub_part_detail,
                            quantity: row.quantity,
                        }]);
                    }
                },
                error: function(xhr) {
                    showApiError(xhr);
                }
            }
        );
    }

    $(table).inventreeTable({
        url: options.url || '{% url "api-bom-list" %}',
        name: options.table_name || 'usedin',
        sortable: true,
        search: true,
        showColumns: true,
        queryParams: filters,
        original: params,
        rootParentId: 'top-level-item',
        idField: 'pk',
        uniqueId: 'pk',
        parentIdField: 'parent',
        treeShowField: 'part',
        onLoadSuccess: function(tableData) {
            // Once the initial data are loaded, check if there are any "inherited" BOM lines
            for (var ii = 0; ii < tableData.length; ii++) {
                var row = tableData[ii];

                // This is a "top level" item in the table
                row.parent = 'top-level-item';

                // Ignore this row as it is not "inherited" by variant parts
                if (!row.inherited) {
                    continue;
                }

                loadVariantData(row);
            }
        },
        onPostBody: function() {
            $(table).treegrid({
                treeColumn: 0,
            });
        },
        columns: [
            {
                field: 'pk',
                title: 'ID',
                visible: false,
                switchable: false,
            },
            {
                field: 'part',
                title: '{% trans "Assembly" %}',
                switchable: false,
                sortable: true,
                formatter: function(value, row) {
                    var url = `/part/${value}/?display=bom`;
                    var html = '';

                    var part = row.part_detail;

                    html += imageHoverIcon(part.thumbnail);
                    html += renderLink(part.full_name, url);
                    html += makePartIcons(part);

                    return html;
                }
            },
            {
                field: 'sub_part',
                title: '{% trans "Required Part" %}',
                sortable: true,
                formatter: function(value, row) {
                    var url = `/part/${value}/`;
                    var html = '';

                    var sub_part = row.sub_part_detail;

                    html += imageHoverIcon(sub_part.thumbnail);
                    html += renderLink(sub_part.full_name, url);
                    html += makePartIcons(sub_part);

                    return html;
                }
            },
            {
                field: 'quantity',
                title: '{% trans "Required Quantity" %}',
                formatter: function(value, row) {
                    var html = value;

                    if (row.parent && row.parent != 'top-level-item') {
                        html += ` <em>({% trans "Inherited from parent BOM" %})</em>`;
                    }

                    return html;
                }
            }
        ]
    });
}
