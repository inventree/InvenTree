{% load i18n %}

/* BOM management functions.
 * Requires follwing files to be loaded first:
 * - api.js
 * - part.js
 * - modals.js
 */


function reloadBomTable(table, options) {

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
            console.log("Row: " + rowNum);
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

    // Construct the table columns

    var cols = [
        {
            field: 'pk',
            title: 'ID',
            visible: false,
        },
    ];

    if (options.editable) {
        
        /*
        // TODO - Enable multi-select functionality 
        cols.push({
            checkbox: true,
            title: 'Select',
            searchable: false,
            sortable: false,
        });
        */
    }


    // Part column
    cols.push(
        {
            field: 'sub_part_detail.full_name',
            title: '{% trans "Part" %}',
            sortable: true,
            formatter: function(value, row, index, field) {
                var url = `/part/${row.sub_part}/`;
                var html = imageHoverIcon(row.sub_part_detail.thumbnail) + renderLink(row.sub_part_detail.full_name, url);

                // Display an extra icon if this part is an assembly
                if (row.sub_part_detail.assembly) {
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
        formatter: function(value, row, index, field) {
            var text = value;

            // The 'value' is a text string with (potentially) multiple trailing zeros
            // Let's make it a bit more pretty
            text = parseFloat(text);

            if (row.overage) {
                text += "<small> (+" + row.overage + ")    </small>";
            }

            return text;
        },
    });

    if (!options.editable) {
        cols.push(
        {
            field: 'sub_part_detail.stock',
            title: '{% trans "Available" %}',
            searchable: false,
            sortable: true,
            formatter: function(value, row, index, field) {

                var url = `/part/${row.sub_part_detail.pk}/stock/`;
                var text = value;

                if (value == null || value <= 0) {
                    text = `<span class='label label-warning'>{% trans "No Stock" %}</span>`;
                }

                return renderLink(text, url);
            }
        });

        cols.push(
        {
            field: 'price_range',
            title: '{% trans "Price" %}',
            sortable: true,
            formatter: function(value, row, index, field) {
                if (value) {
                    return value;
                } else {
                    return "<span class='warning-msg'>{% trans "No pricing available" %}</span>";
                }
            }
        });
    }
    
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
            formatter: function(value, row, index, field) {

                var bValidate = "<button title='{% trans "Validate BOM Item" %}' class='bom-validate-button btn btn-default btn-glyph' type='button' pk='" + row.pk + "'><span class='fas fa-check-circle icon-blue'/></button>";
                var bValid = "<span title='{% trans "This line has been validated" %}' class='fas fa-check-double icon-green'/>";

                var bEdit = "<button title='{% trans "Edit BOM Item" %}' class='bom-edit-button btn btn-default btn-glyph' type='button' url='/part/bom/" + row.pk + "/edit'><span class='fas fa-edit'/></button>";
                var bDelt = "<button title='{% trans "Delete BOM Item" %}' class='bom-delete-button btn btn-default btn-glyph' type='button' url='/part/bom/" + row.pk + "/delete'><span class='fas fa-trash-alt icon-red'/></button>";
                
                var html = "<div class='btn-group' role='group'>";
                
                html += bEdit;
                html += bDelt;
                
                if (!row.validated) {
                    html += bValidate;
                } else {
                    html += bValid;
                }

                html += "</div>";

                return html;
            }
        });
    }

    // Configure the table (bootstrap-table)

    var params = {
        part: options.parent_id,
        ordering: 'name',
    }

    if (options.part_detail) {
        params.part_detail = true;
    }

    if (options.sub_part_detail) {
        params.sub_part_detail = true;
    }
    
    table.bootstrapTable({
        sortable: true,
        search: true,
        rowStyle: function(row, index) {
            if (row.validated) {
                return {classes: 'rowvalid'};
            } else {
                return {classes: 'rowinvalid'};
            }
        },
        formatNoMatches: function() { return "{% trans "No BOM items found" %}"; },
        clickToSelect: true,
        queryParams: function(p) {
            return params;
        },
        columns: cols,
        url: options.bom_url
    });

    // In editing mode, attached editables to the appropriate table elements
    if (options.editable) {

        table.on('click', '.bom-delete-button', function() {
            var button = $(this);
            
            launchModalForm(button.attr('url'), {
                                success: function() {
                                    reloadBomTable(table);
                                }
            });
        });

        table.on('click', '.bom-edit-button', function() {
            var button = $(this);

            launchModalForm(button.attr('url'), {
                                success: function() {
                                    reloadBomTable(table);
                                }
            });
        });

        table.on('click', '.bom-validate-button', function() {
            var button = $(this);

            var url = '/api/bom/' + button.attr('pk') + '/validate/';

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