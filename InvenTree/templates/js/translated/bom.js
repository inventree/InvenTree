{% load i18n %}

/* globals
    constructForm,
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
    newPartFromBomWizard,
    loadBomTable,
    removeRowFromBomWizard,
    removeColFromBomWizard,
*/

/* BOM management functions.
 * Requires follwing files to be loaded first:
 * - api.js
 * - part.js
 * - modals.js
 */


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


function loadBomTable(table, options) {
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

    if (!show_pricing) {
        params.include_pricing = false;
    }

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
            title: '{% trans "Part" %}',
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
    });

    cols.push({
        field: 'sub_part_detail.stock',
        title: '{% trans "Available" %}',
        searchable: false,
        sortable: true,
        formatter: function(value, row) {

            var url = `/part/${row.sub_part_detail.pk}/?display=part-stock`;
            var text = value;

            if (value == null || value <= 0) {
                text = `<span class='label label-warning'>{% trans "No Stock" %}</span>`;
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
            if (row.substitutes) {
                return row.substitutes.length;
            } else {
                return '-';
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
                return '{% trans "Inherited" %}';
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

                if (row.quantity > 0) {
                    can_build = row.sub_part_detail.stock / row.quantity;
                }

                return +can_build.toFixed(2);
            },
            sorter: function(valA, valB, rowA, rowB) {
                // Function to sort the "can build" quantity
                var cb_a = 0;
                var cb_b = 0;

                if (rowA.quantity > 0) {
                    cb_a = rowA.sub_part_detail.stock / rowA.quantity;
                }

                if (rowB.quantity > 0) {
                    cb_b = rowB.sub_part_detail.stock / rowB.quantity;
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

                    var bValidate = `<button title='{% trans "Validate BOM Item" %}' class='bom-validate-button btn btn-default btn-glyph' type='button' pk='${row.pk}'><span class='fas fa-check-circle icon-blue'/></button>`;

                    var bValid = `<span title='{% trans "This line has been validated" %}' class='fas fa-check-double icon-green'/>`;

                    var bEdit = `<button title='{% trans "Edit BOM Item" %}' class='bom-edit-button btn btn-default btn-glyph' type='button' pk='${row.pk}'><span class='fas fa-edit'></span></button>`;

                    var bDelt = `<button title='{% trans "Delete BOM Item" %}' class='bom-delete-button btn btn-default btn-glyph' type='button' pk='${row.pk}'><span class='fas fa-trash-alt icon-red'></span></button>`;

                    var html = `<div class='btn-group' role='group'>`;

                    html += bEdit;
                    html += bDelt;

                    if (!row.validated) {
                        html += bValidate;
                    } else {
                        html += bValid;
                    }

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
    function requestSubItems(bom_pk, part_pk) {

        inventreeGet(
            options.bom_url,
            {
                part: part_pk,
                sub_part_detail: true,
            },
            {
                success: function(response) {
                    for (var idx = 0; idx < response.length; idx++) {

                        response[idx].parentId = bom_pk;

                        if (response[idx].sub_part_detail.assembly) {
                            requestSubItems(response[idx].pk, response[idx].sub_part);
                        }
                    }

                    table.bootstrapTable('append', response);

                    table.treegrid('collapseAll');
                },
                error: function() {
                    console.log('Error requesting BOM for part=' + part_pk);
                }
            }
        );
    }

    table.inventreeTable({
        treeEnable: !options.editable,
        rootParentId: parent_id,
        idField: 'pk',
        parentIdField: 'parentId',
        treeShowField: 'sub_part',
        showColumns: true,
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
        clickToSelect: true,
        queryParams: filters,
        original: params,
        columns: cols,
        url: options.bom_url,
        onPostBody: function() {

            if (!options.editable) {
                table.treegrid({
                    treeColumn: 0,
                    onExpand: function() {
                    }
                });
            }
        },
        onLoadSuccess: function() {

            if (options.editable) {
                table.bootstrapTable('uncheckAll');
            } else {

                var data = table.bootstrapTable('getData');

                for (var idx = 0; idx < data.length; idx++) {
                    var row = data[idx];

                    // If a row already has a parent ID set, it's already been updated!
                    if (row.parentId) {
                        continue;
                    }

                    // Set the parent ID of the top-level rows
                    row.parentId = parent_id;

                    table.bootstrapTable('updateRow', idx, row, true);

                    if (row.sub_part_detail.assembly) {
                        requestSubItems(row.pk, row.sub_part);
                    }
                }
            }
        },
    });

    // In editing mode, attached editables to the appropriate table elements
    if (options.editable) {

        table.on('click', '.bom-delete-button', function() {

            var pk = $(this).attr('pk');

            constructForm(`/api/bom/${pk}/`, {
                method: 'DELETE',
                title: '{% trans "Delete BOM Item" %}',
                onSuccess: function() {
                    reloadBomTable(table);
                }
            }); 
        });

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
    }
}
