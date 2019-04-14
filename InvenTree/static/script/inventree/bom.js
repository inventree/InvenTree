/* BOM management functions.
 * Requires follwing files to be loaded first:
 * - api.js
 * - part.js
 * - modals.js
 */


function refreshBOM(){
    // TODO - Update the BOM data once the data are read from the server
}


function editBOM(options){

    /* Launch a modal window to edit the BOM options.
     * The caller should pass the following key:value data in 'options':
     * part_name: The name of the part being edited
     * part_id: The pk of the part (for AJAX lookup)
     * url: The JSON API URL to get BOM data
     */

    // Default modal target if none is supplied
    var modal = options.modal || '#modal-form';
    
    var title = 'Edit BOM for ' + options.part_name;

    var body = `
        <table class='table table-striped table-condensed' id='modal-bom-table'></table>
        <div style='float: right;'>
            <button class='btn btn-basic' type='button' id='new-bom-item'>Add BOM Item</button>
        </div>
    `;

    openModal(
        {
            modal: modal,
            content: body,
            title: title,
            submit_text: 'Save',
            close_text: 'Cancel',
        }
    );

    $('#new-bom-item').click(function() {
        alert("New BOM item!");
    });

    $('#modal-bom-table').bootstrapTable({
        sortable: true,
        search: true,
        queryParams: function(p) {
            return {
                part: options.part_id,
            }
        },
        //data: {},
        columns: [
            {
                field: 'pk',
                title: 'ID',
                visible: false
            },
            {
                field: 'sub_part.name',
                title: 'Part',
                sortable: true,
            },
            {
                field: 'sub_part.description',
                title: 'Description',
            },
            {
                field: 'quantity',
                title: 'Required',
                searchable: false,
                sortable: true,
            }
        ],
        url: options.url,
    });
}