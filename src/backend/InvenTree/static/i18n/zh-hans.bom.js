

/* globals
    addFieldErrorMessage,
    constructField,
    constructForm,
    constructFormBody,
    createNewModal,
    enableSubmitButton,
    exportFormatOptions,
    formatDecimal,
    formatPriceRange,
    getApiEndpointOptions,
    getFormFieldValue,
    handleFormErrors,
    handleFormSuccess,
    imageHoverIcon,
    initializeRelatedField,
    inventreeGet,
    inventreeLoad,
    inventreePut,
    inventreeSave,
    launchModalForm,
    loadTableFilters,
    makeDeleteButton,
    makeEditButton,
    makeIcon,
    makeIconBadge,
    makeIconButton,
    makeInfoButton,
    makePartIcons,
    makeRemoveButton,
    modalSetContent,
    partFields,
    partGroups,
    reloadBootstrapTable,
    renderLink,
    setupFilterList,
    shortenString,
    showApiError,
    thumbnailImage,
    updateFieldValue,
    withTitle,
    wrapButtons,
    yesNoLabel,
*/

/* exported
    addBomItem,
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


/*
 * Launch a dialog to add a new BOM line item to a Bill of Materials
 */
function addBomItem(part_id, options={}) {

    var fields = bomItemFields();

    fields.part.value = part_id;
    fields.sub_part.filters = {
        active: true,
    };

    constructForm('/api/bom/', {
        fields: fields,
        method: 'POST',
        title: '创建物料清单项目',
        focus: 'sub_part',
        onSuccess: function(response) {
            handleFormSuccess(response, options);
        }
    });
}


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

        let buttons = '';

        buttons += makeInfoButton('button-row-data', idx, '显示行数据');
        buttons += makeRemoveButton('button-row-remove', idx, '移除行');

        buttons = wrapButtons(buttons);

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
                api_url: '/api/part/',
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
                title: '行数据',
                closeText: '关闭',
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
    getApiEndpointOptions('/api/bom/', function(response) {

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

    var url = '/api/bom/import/submit/';

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

    var opts = {
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
                    handleFormErrors(xhr.responseJSON, fields, opts);
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
        title: '下载物料清单模板',
        fields: {
            format: {
                label: '格式',
                help_text: '选择文件格式',
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
            location.href = `/api/part/bom_template/?format=${format}`;

        }
    });
}


/**
 * Export BOM (Bill of Materials) for the specified Part instance
 */
function exportBom(part_id, options={}) {

    constructFormBody({}, {
        title: '输出物料清单',
        fields: {
            format: {
                label: '格式',
                help_text: '选择文件格式',
                required: true,
                type: 'choice',
                value: inventreeLoad('bom-export-format', 'csv'),
                choices: exportFormatOptions(),
            },
            cascade: {
                label: '多级物料清单',
                help_text: '包括子装配体物料清单数据',
                type: 'boolean',
                value: inventreeLoad('bom-export-cascading', true),
            },
            levels: {
                label: '等级',
                help_text: '选择要导出的物料清单的最大级别 (0 = 所有级别)',
                type: 'integer',
                value: 0,
                required: true,
                min_value: 0,
            },
            substitute_part_data: {
                label: '包含替代零件',
                help_text: '在导出的物料清单中包含替代零件',
                type: 'boolean',
                value: inventreeLoad('bom-export-substitute_part_data', false),
            },
            parameter_data: {
                label: '包含参数数据',
                help_text: '在导出的物料清单中包含零件参数',
                type: 'boolean',
                value: inventreeLoad('bom-export-parameter_data', false),
            },
            stock_data: {
                label: '包括库存数据',
                help_text: '在导出的物料清单中包含零件库存数据',
                type: 'boolean',
                value: inventreeLoad('bom-export-stock_data', false),
            },
            manufacturer_data: {
                label: '包括制造商数据',
                help_text: '在导出的物料清单中包含零件制造商数据',
                type: 'boolean',
                value: inventreeLoad('bom-export-manufacturer_data', false),
            },
            supplier_data: {
                label: '包含供应商数据',
                help_text: '在导出的物料清单中包含零件供应商数据',
                type: 'boolean',
                value: inventreeLoad('bom-export-supplier_data', false),
            },
            pricing_data: {
                label: '包含价格数据',
                help_text: '在导出的物料清单中包含零件价格数据',
                type: 'boolean',
                value: inventreeLoad('bom-export-pricing_data', false),
            }
        },
        onSubmit: function(fields, opts) {

            // Extract values from the form
            var field_names = [
                'format', 'cascade', 'levels',
                'substitute_part_data',
                'parameter_data',
                'stock_data',
                'manufacturer_data',
                'supplier_data',
                'pricing_data',
            ];

            var url = `/api/part/${part_id}/bom-download/?`;

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
            icon: 'fa-shapes',
            secondary: {
                title: '新零件',
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
        note: {
            icon: 'fa-sticky-note',
        },
        allow_variants: {},
        inherited: {},
        consumable: {},
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

        buttons += makeRemoveButton('button-row-remove', pk, '移除替代品零件');

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
    <strong>基础零件</strong><hr>
    ${part_thumb} ${part_name} - <em>${part_desc}</em>
    </div>
    `;

    // Add a table of individual rows
    html += `
    <table class='table table-striped table-condensed' id='substitute-table'>
        <thead>
            <tr>
                <th>零件</th>
                <th>描述</th>
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
        使用下面的输入选择并添加新的替代品零件
    </div>
    `;

    // Add a callback to remove a row from the table
    function addRemoveCallback(modal, element) {
        $(modal).find(element).click(function() {
            var pk = $(this).attr('pk');

            var pre = `
            <div class='alert alert-block alert-warning'>
            您确定要删除此替代品零件链接吗？
            </div>
            `;

            constructForm(`/api/bom/substitute/${pk}/`, {
                method: 'DELETE',
                title: '移除替代品零件',
                preFormContent: pre,
                confirm: true,
                onSuccess: function() {
                    $(modal).find(`#substitute-row-${pk}`).remove();
                    reloadParentTable();
                }
            });
        });
    }

    constructForm('/api/bom/substitute/', {
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
        closeText: '关闭',
        submitText: '添加替代品',
        title: '编辑物料清单项替代品',
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
    所有选定的物料清单项目都将被删除
    </div>

    <table class='table table-striped table-condensed'>
        <tr>
            <th>零件</th>
            <th>參考代號</th>
            <th>數量</th>
        </tr>
        ${rows}
    </table>
    `;

    constructForm('/api/bom/', {
        method: 'DELETE',
        multi_delete: true,
        title: '删除选中的物料清单项目吗？',
        form_data: {
            items: ids,
        },
        preFormContent: html,
        onSuccess: options.success,
    });
}


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
function loadBomTable(table, options={}) {

    var params = {
        part: options.parent_id,
        ordering: 'name',
    };

    if (options.part_detail) {
        params.part_detail = true;
    }

    params.sub_part_detail = true;

    var filters = {};

    if (!options.disableFilters) {
        filters = loadTableFilters('bom');
    }

    Object.assign(filters, params);

    setupFilterList('bom', $(table), '#filter-list-bom', {
        custom_actions: [{
            label: 'actions',
            actions: [{
                label: 'delete',
                title: '删除项目',
                icon: 'fa-trash-alt icon-red',
                permission: 'part.change',
                callback: function(data) {
                    deleteBomItems(data, {
                        success: function() {
                            reloadBootstrapTable('#bom-table');
                        }
                    });
                }
            }]
        }]
    });

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

    function canBuildQuantity(row) {
        // Calculate how many of each row we can make, given current stock

        if (row.consumable) {
            // If the row is "consumable" we do not 'track' the quantity
            return Infinity;
        }

        // Prevent div-by-zero or negative errors
        if ((row.quantity || 0) <= 0) {
            return 0;
        }

        return availableQuantity(row) / row.quantity;
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
            field: 'sub_part',
            title: '零件',
            sortable: true,
            switchable: false,
            sorter: function(_valA, _valB, rowA, rowB) {
                let name_a = rowA.sub_part_detail.full_name;
                let name_b = rowB.sub_part_detail.full_name;

                if (name_a > name_b) {
                    return 1;
                } else if (name_a < name_b) {
                    return -1;
                } else {
                    return 0;
                }
            },
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
                                <span class='fas fa-sync-alt' title='为子组件加载物料清单'></span>
                            </a> `;
                    }
                }

                html += imageHoverIcon(sub_part.thumbnail) + renderLink(row.sub_part_detail.full_name, url);

                html += makePartIcons(sub_part);

                if (row.substitutes && row.substitutes.length > 0) {
                    html += makeIconBadge('fa-exchange-alt', '替代品可用');
                }

                if (row.allow_variants) {
                    html += makeIconBadge('fa-sitemap', '已允许变体库存');
                }

                return html;
            }
        }
    );


    // Part description
    cols.push(
        {
            field: 'sub_part_detail.description',
            title: '描述',
            formatter: function(value) {
                return withTitle(shortenString(value), value);
            }
        }
    );

    // Part reference
    cols.push({
        field: 'reference',
        title: '參考代號',
        searchable: true,
        sortable: true,
    });

    // Part quantity
    cols.push({
        field: 'quantity',
        title: '數量',
        searchable: false,
        sortable: true,
        switchable: false,
        formatter: function(value, row) {
            var text = value;

            // The 'value' is a text string with (potentially) multiple trailing zeros
            // Let's make it a bit more pretty
            text = parseFloat(text);

            if (row.sub_part_detail && row.sub_part_detail.units) {
                text += ` <small>${row.sub_part_detail.units}</small>`;
            }

            if (row.consumable) {
                text += ` <small>(耗材)</small>`;
            }

            if (row.optional) {
                text += ' <small>(非必須項目)</small>';
            }

            if (row.overage) {
                text += `<small> (+${row.overage})</small>`;
            }

            return text;
        },
    });

    cols.push({
        field: 'substitutes',
        title: '替代品',
        searchable: false,
        sortable: true,
        formatter: function(value, row) {
            if (row.substitutes && row.substitutes.length > 0) {
                return row.substitutes.length;
            } else {
                return yesNoLabel(false);
            }
        }
    });

    cols.push({
        field: 'optional',
        title: '非必須項目',
        searchable: false,
        formatter: function(value) {
            return yesNoLabel(value);
        }
    });

    cols.push({
        field: 'consumable',
        title: '耗材',
        searchable: false,
        formatter: function(value) {
            return yesNoLabel(value);
        }
    });

    cols.push({
        field: 'allow_variants',
        title: '允许变体',
        formatter: function(value) {
            return yesNoLabel(value);
        }
    });

    cols.push({
        field: 'inherited',
        title: '获取继承的',
        searchable: false,
        formatter: function(value, row) {
            // This BOM item *is* inheritable, but is defined for this BOM
            if (!row.inherited) {
                return yesNoLabel(false);
            } else if (row.part == options.parent_id) {
                return yesNoLabel(true);
            } else {
                // If this BOM item is inherited from a parent part
                return yesNoLabel(true, {muted: true});
            }
        }
    });

    cols.push({
        field: 'pricing',
        title: '价格范围',
        sortable: true,
        sorter: function(valA, valB, rowA, rowB) {
            var a = rowA.pricing_min || rowA.pricing_max;
            var b = rowB.pricing_min || rowB.pricing_max;

            if (a != null) {
                a = parseFloat(a) * rowA.quantity;
            }

            if (b != null) {
                b = parseFloat(b) * rowB.quantity;
            }

            return (a > b) ? 1 : -1;
        },
        formatter: function(value, row) {

            return formatPriceRange(
                row.pricing_min,
                row.pricing_max,
                {
                    quantity: row.quantity
                }
            );
        },
        footerFormatter: function(data) {
            // Display overall price range the "footer" of the price_range column

            var min_price = 0;
            var max_price = 0;

            var any_pricing = false;
            var complete_pricing = true;

            for (var idx = 0; idx < data.length; idx++) {

                var row = data[idx];

                // Do not include pricing for items which are associated with sub-assemblies
                if (row.parentId != parent_id) {
                    continue;
                }

                // No pricing data available for this row
                if (row.pricing_min == null && row.pricing_max == null) {
                    complete_pricing = false;
                    continue;
                }

                // At this point, we have at least *some* information
                any_pricing = true;

                // Extract min/max values for this row
                var row_min = row.pricing_min || row.pricing_max;
                var row_max = row.pricing_max || row.pricing_min;

                min_price += parseFloat(row_min) * row.quantity;
                max_price += parseFloat(row_max) * row.quantity;
            }

            if (any_pricing) {

                let html = formatPriceRange(min_price, max_price);

                if (complete_pricing) {
                    html += makeIconBadge(
                        'fa-check-circle icon-green',
                        '物料清单定价已完成',
                    );
                } else {
                    html += makeIconBadge(
                        'fa-exclamation-circle icon-yellow',
                        '物料清单定价未完成',
                    );
                }

                return html;

            } else {
                let html = '<em>无可用价格</em>';
                html += makeIconBadge('fa-times-circle icon-red');

                return html;
            }
        }
    });


    cols.push({
        field: 'available_stock',
        title: '可用數量',
        searchable: false,
        sortable: true,
        formatter: function(value, row) {

            var url = `/part/${row.sub_part_detail.pk}/?display=part-stock`;

            // Calculate total "available" (unallocated) quantity
            var substitute_stock = row.available_substitute_stock || 0;
            var variant_stock = row.allow_variants ? (row.available_variant_stock || 0) : 0;

            var available_stock = availableQuantity(row);

            var external_stock = row.external_stock ?? 0;

            var text = renderLink(`${available_stock}`, url);

            if (row.sub_part_detail && row.sub_part_detail.units) {
                text += ` <small>${row.sub_part_detail.units}</small>`;
            }

            if (external_stock > 0) {
                text += makeIconBadge('fa-sitemap', `外部库存: ${external_stock}`);
            }

            if (available_stock <= 0) {
                text += makeIconBadge('fa-times-circle icon-red', '无可用库存');
            } else {
                var extra = '';

                if ((substitute_stock > 0) && (variant_stock > 0)) {
                    extra = '包括变体和替代品库存';
                } else if (variant_stock > 0) {
                    extra = '包括变体库存';
                } else if (substitute_stock > 0) {
                    extra = '包括替代品库存';
                }

                if (extra) {
                    text += `<span title='${extra}' class='fas fa-info-circle float-right icon-blue'></span>`;
                }
            }

            if (row.on_order && row.on_order > 0) {
                text += makeIconBadge(
                    'fa-shopping-cart',
                    `已订购: ${row.on_order}`,
                );
            }

            return text;
        }
    });

    cols.push(
        {
            field: 'can_build',
            title: '可以创建',
            sortable: true,
            formatter: function(value, row) {

                // "Consumable" parts are not tracked in the build
                if (row.consumable) {
                    return `<em>消耗品</em>`;
                }

                var can_build = canBuildQuantity(row);

                return +can_build.toFixed(2);
            },
            sorter: function(valA, valB, rowA, rowB) {
                // Function to sort the "can build" quantity
                var cb_a = canBuildQuantity(rowA);
                var cb_b = canBuildQuantity(rowB);

                return (cb_a > cb_b) ? 1 : -1;
            },
            footerFormatter: function(data) {
                var can_build = null;

                data.forEach(function(row) {
                    if (row.quantity > 0 && !row.consumable) {
                        var cb = availableQuantity(row) / row.quantity;

                        if (can_build == null || cb < can_build) {
                            can_build = cb;
                        }
                    }
                });

                if (can_build == null) {
                    return '-';
                } else {
                    return formatDecimal(can_build, 2);
                }
            }
        }
    );

    // Part notes
    cols.push(
        {
            field: 'note',
            title: '备注',
            searchable: true,
            sortable: true,
            formatter: function(value) {
                return withTitle(shortenString(value), value);
            }
        }
    );

    if (options.editable) {

        cols.push({
            title: '动作',
            switchable: false,
            field: 'pk',
            visible: true,
            formatter: function(value, row) {

                if (row.part == options.parent_id) {

                    var bValidate = makeIconButton('fa-check-circle icon-green', 'bom-validate-button', row.pk, '验证物料清单项目');

                    var bValid = makeIconButton('fa-check-double icon-green', 'bom-valid-button', row.pk, '此行已验证', {disabled: true});

                    var bSubs = makeIconButton('fa-exchange-alt icon-blue', 'bom-substitutes-button', row.pk, '编辑替代品零件');

                    var bEdit = makeEditButton('bom-edit-button', row.pk, '编辑物料清单项目');

                    var bDelt = makeDeleteButton('bom-delete-button', row.pk, '删除物料清单项目');

                    let buttons = '';

                    if (!row.validated) {
                        buttons += bValidate;
                    } else {
                        buttons += bValid;
                    }

                    buttons += bEdit;
                    buttons += bSubs;
                    buttons += bDelt;

                    return wrapButtons(buttons);

                } else {
                    // Return a link to the external BOM

                    return renderLink(
                        '查看物料清单',
                        `/part/${row.part}/?display=bom`
                    );
                }
            },
            footerFormatter: function(data) {
                return `
                <button class='btn btn-success float-right' type='button' title='添加物料清单项' id='bom-item-new-footer'>
                    ${makeIcon('fa-plus-circle')} 添加物料清单项
                </button>
                `;
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
            },
            {
                success: function(response) {

                    // Add the returned sub-items to the table
                    for (var idx = 0; idx < response.length; idx++) {
                        response[idx].parentId = bom_pk;
                    }

                    var row = table.bootstrapTable('getRowByUniqueId', bom_pk);
                    row.sub_assembly_received = true;

                    table.bootstrapTable('updateByUniqueId', bom_pk, row, true);

                    table.bootstrapTable('append', response);

                    // Auto-expand the newly added row
                    $(`.treegrid-${bom_pk}`).treegrid('expand');
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
            return '未找到物料清单项目';
        },
        queryParams: filters,
        original: params,
        columns: cols,
        url: options.bom_url,
        onPostBody: function() {

            table.treegrid({
                treeColumn: 1,
            });

            table.treegrid('collapseAll');

            // Callback for 'load sub assembly' button
            table.find('.load-sub-assembly').click(function(event) {

                event.preventDefault();

                var pk = $(this).attr('pk');
                var row = table.bootstrapTable('getRowByUniqueId', pk);

                // Request BOM data for this subassembly
                requestSubItems(row.pk, row.sub_part);

                row.sub_assembly_requested = true;
                table.bootstrapTable('updateByUniqueId', pk, row, true);
            });

            var data = table.bootstrapTable('getData');

            var update_required = false;

            for (var idx = 0; idx < data.length; idx++) {

                if (!data[idx].parentId) {
                    data[idx].parentId = parent_id;
                    update_required = true;
                }
            }

            // Re-load the table back data
            if (update_required) {
                table.bootstrapTable('load', data);
            }
        },
        onLoadSuccess: function(data) {

            if (options.editable) {
                table.bootstrapTable('uncheckAll');
            }
        },
    });

    // In editing mode, attached editables to the appropriate table elements
    if (options.editable) {

        // Callback for "new bom item" button in footer
        table.on('click', '#bom-item-new-footer', function() {
            addBomItem(options.parent_id, {
                onSuccess: function() {
                    table.bootstrapTable('refresh');
                }
            });
        });

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
                title: '编辑物料清单项目',
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
    params.sub_part_detail = true;

    var filters = loadTableFilters('usedin', params);

    setupFilterList('usedin', $(table), options.filterTarget || '#filter-list-usedin');

    function loadVariantData(row) {
        // Load variants information for inherited BOM rows

        inventreeGet(
            '/api/part/',
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
        url: options.url || '/api/bom/',
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
                title: '装配',
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
                title: '必须零件',
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
                title: '所需数量',
                formatter: function(value, row) {
                    var html = value;

                    if (row.sub_part_detail && row.sub_part_detail.units) {
                        html += ` <small>${row.sub_part_detail.units}</small>`;
                    }

                    if (row.parent && row.parent != 'top-level-item') {
                        html += ` <em>(从上级物料清单继承)</em>`;
                    }

                    return html;
                }
            }
        ]
    });
}
