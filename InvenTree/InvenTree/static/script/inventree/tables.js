function editButton(url, text='Edit') {
    return "<button class='btn btn-success edit-button btn-sm' type='button' url='" + url + "'>" + text + "</button>";
}


function deleteButton(url, text='Delete') {
    return "<button class='btn btn-danger delete-button btn-sm' type='button' url='" + url + "'>" + text + "</button>";
}


function renderLink(text, url) {
    if (text === '' || url === '') {
        return text;
    }

    return '<a href="' + url + '">' + text + '</a>';
}


function enableButtons(elements, enabled) {
    for (let item of elements) {
        $(item).prop('disabled', !enabled);
    }
}


function linkButtonsToSelection(table, buttons) {
    /* Link a bootstrap-table object to one or more buttons.
     * The buttons will only be enabled if there is at least one row selected
     */

    // Initially set the enable state of the buttons
    enableButtons(buttons, table.bootstrapTable('getSelections').length > 0);

    // Add a callback
    table.on('check.bs.table uncheck.bs.table check-some.bs.table uncheck-some.bs.table check-all.bs.table uncheck-all.bs.table', function(row) {
        enableButtons(buttons, table.bootstrapTable('getSelections').length > 0);
    });
}


function isNumeric(n) {
    return !isNaN(parseFloat(n)) && isFinite(n);
}


/*
 * Reload a table which has already been made into a bootstrap table.
 * New filters can be optionally provided, to change the query params.
 */
function reloadTable(table, filters) {

    // Simply perform a refresh
    if (filters == null) {
        table.bootstrapTable('refresh');
        return;
    }

    // More complex refresh with new filters supplied
    var options = table.bootstrapTable('getOptions');

    // Construct a new list of filters to use for the query
    var params = {};

    for (var key in filters) {
        params[key] = filters[key];
    }

    // Original query params will override
    if (options.original != null) {
        for (var key in options.original) {
            params[key] = options.original[key];
        }
    }

    options.queryParams = params;

    table.bootstrapTable('refreshOptions', options);
    table.bootstrapTable('refresh');
}


/* Wrapper function for bootstrapTable.
 * Sets some useful defaults, and manage persistent settings.
 */
$.fn.inventreeTable = function(options) {

    var tableName = options.name || 'table';

    var varName = tableName + '-pagesize';

    options.pagination = true;
    options.pageSize = inventreeLoad(varName, 25);
    options.pageList = [25, 50, 100, 250, 'all'];
    options.rememberOrder = true;
    options.sortable = true;
    options.search = true;

    // Callback to save pagination data
    options.onPageChange = function(number, size) {
        inventreeSave(varName, size);
    };

    // Standard options for all tables
    this.bootstrapTable(options);
}

function customGroupSorter(sortName, sortOrder, sortData) {

    var order = sortOrder === 'desc' ? -1 : 1;

    sortData.sort(function(a, b) {

        // Extract default field values
        var aa = a[sortName];
        var bb = b[sortName];

        // Extract parent information
        var aparent = a._data && a._data['parent-index'];
        var bparent = b._data && b._data['parent-index'];

        // If either of the comparisons are in a group
        if (aparent || bparent) {

            // If the parents are different (or one item does not have a parent,
            // then we need to extract the parent value for the selected column.

            if (aparent != bparent) {
                if (aparent) {
                    aa = a._data['table'].options.groupByFormatter(sortName, 0, a._data['group-data']);
                }

                if (bparent) {
                    bb = b._data['table'].options.groupByFormatter(sortName, 0, b._data['group-data']);
                }
            }
        }

        if (aa === undefined || aa === null) {
            aa = '';
        }
        if (bb === undefined || bb === null) {
            bb = '';
        }

        if (isNumeric(aa) && isNumeric(bb)) {
            if (aa < bb) {
                return order * -1;
            } else if (aa > bb) {
                return order;
            } else {
                return 0;
            }
        }

        aa = aa.toString();
        bb = bb.toString();

        var cmp = aa.localeCompare(bb);
        
        if (cmp === -1) {
            return order * -1;
        } else if (cmp === 1) {
            return order;
        } else {
            return 0;
        }
    });
}