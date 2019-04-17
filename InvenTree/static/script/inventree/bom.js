/* BOM management functions.
 * Requires follwing files to be loaded first:
 * - api.js
 * - part.js
 * - modals.js
 */


function reloadBomTable(table, options) {

    table.bootstrapTable('refresh');
}


function downloadBom(options = {}) {

    var modal = options.modal || "#modal-form";
    
    var content = `
        <b>Select file format</b><br>
        <div class='controls'>
        <select id='bom-format' class='select'>
            <option value='csv'>CSV</option>
            <option value='xls'>XLSX</option>
            <option value='yaml'>YAML</option>
            <option value='json'>JSON</option>
            <option value='xml'>XML</option>
            <option value='html'>HTML</option>
        </select>
        </div>
    `;

    openModal({
        modal: modal,
        title: "Export Bill of Materials",
        submit_text: "Download",
        close_text: "Cancel",
    });

    modalSetContent(modal, content);

    $(modal).on('click', '#modal-form-submit', function() {
        $(modal).modal('hide');

        var format = $(modal).find('#bom-format :selected').val();

        if (options.url) {
            var url = options.url + "?format=" + format;

            location.href = url;
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
        }
    ];

    if (options.editable) {
        cols.push({
            formatter: function(value, row, index, field) {
                var bEdit = "<button class='btn btn-success bom-edit-button btn-sm' type='button' url='" + row.url + "edit'>Edit</button>";
                var bDelt = "<button class='btn btn-danger bom-delete-button btn-sm' type='button' url='" + row.url + "delete'>Delete</button>";

                return "<div class='btn-group'>" + bEdit + bDelt + "</div>";
            }
        });
    }

    // Part column
    cols.push(
        {
            field: 'sub_part',
            title: 'Part',
            sortable: true,
            formatter: function(value, row, index, field) {
                return renderLink(value.name, value.url);
            }
        }
    );

    // Part description
    cols.push(
        {
            field: 'sub_part.description',
            title: 'Description',
        }
    );

    // Part quantity
    cols.push(
        {
            field: 'quantity',
            title: 'Required',
            searchable: false,
            sortable: true,
        }
    );

    // Part notes
    cols.push(
        {
            field: 'note',
            title: 'Notes',
            searchable: true,
            sortable: false,
        }
    );

    // If we are NOT editing, display the available stock
    if (!options.editable) {
        cols.push(
            {
                field: 'sub_part.available_stock',
                title: 'Available',
                searchable: false,
                sortable: true,
                formatter: function(value, row, index, field) {
                    var text = "";

                    if (row.quantity < row.sub_part.available_stock)
                    {
                        text = "<span class='label label-success'>" + value + "</span>";
                    }
                    else
                    {
                        text = "<span class='label label-warning'>" + value + "</span>";
                    }

                    return renderLink(text, row.sub_part.url + "stock/");
                }
            }
        );
    }

    // Configure the table (bootstrap-table)

    table.bootstrapTable({
        sortable: true,
        search: true,
        clickToSelect: true,
        queryParams: function(p) {
            return {
                part: options.parent_id,
            }
        },
        columns: cols,
        url: options.bom_url
    });

    // In editing mode, attached editables to the appropriate table elements
    if (options.editable) {

        table.on('click', '.bom-delete-button', function() {
            var button = $(this);
            
            launchDeleteForm(button.attr('url'), {
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
    }
}