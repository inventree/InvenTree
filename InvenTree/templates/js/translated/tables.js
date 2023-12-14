{% load i18n %}

/* global
    constructFormBody,
    exportFormatOptions,
    getFormFieldValue,
    inventreeLoad,
    inventreeSave,
    sanitizeData,
    sanitizeInputString,
    user_settings,
*/

/* exported
    customGroupSorter,
    downloadTableData,
    getTableData,
    reloadBootstrapTable,
    renderLink,
    reloadTableFilters,
    constructExpandCollapseButtons,
    constructOrderTableButtons,
*/

/**
 * Reload a named table
 * @param table
 */
function reloadBootstrapTable(table) {

    let tbl = table;

    if (tbl) {
        if (typeof tbl === 'string' || tbl instanceof String) {
            tbl = $(tbl);
        }

        if (tbl.exists()) {
            tbl.bootstrapTable('refresh');
        } else {
            console.error(`Invalid table name passed to reloadBootstrapTable(): ${table}`);
        }
    } else {
        console.error(`Null value passed to reloadBootstrapTable()`);
    }
}


/*
 * Construct a set of extra buttons to display against a list of orders,
 * allowing the orders to be displayed in various 'view' modes:
 *
 * - Calendar view
 * - List view
 * - Tree view
 *
 * Options:
 * - callback: Callback function to be called when one of the buttons is pressed
 * - prefix: The prefix to use when saving display data to user session
 * - display: Which button to set as 'active' by default
 *
 */
function constructOrderTableButtons(options={}) {

    var display_mode = options.display;

    var key = `${options.prefix || 'order'}-table-display-mode`;

    // If display mode is not provided, look up from session
    if (!display_mode) {
        display_mode = inventreeLoad(key, 'list');
    }

    var idx = 0;
    var buttons = [];

    function buttonCallback(view_mode) {
        inventreeSave(key, view_mode);

        if (options.callback) {
            options.callback(view_mode);
        }
    }

    var class_calendar = display_mode == 'calendar' ? 'btn-secondary' : 'btn-outline-secondary';
    var class_list = display_mode == 'list' ? 'btn-secondary' : 'btn-outline-secondary';
    var class_tree = display_mode == 'tree' ? 'btn-secondary' : 'btn-outline-secondary';

    // Calendar view button
    if (!options.disableCalendarView) {
        buttons.push({
            html: `<button type='button' name='${idx++}' class='btn ${class_calendar}' title='{% trans "Display calendar view" %}'><span class='fas fa-calendar-alt'></span></button>`,
            event: function() {
                buttonCallback('calendar');
            }
        });
    }

    // List view button
    if (!options.disableListView) {
        buttons.push({
            html: `<button type='button' name='${idx++}' class='btn ${class_list}' title='{% trans "Display list view" %}'><span class='fas fa-th-list'></span></button>`,
            event: function() {
                buttonCallback('list');
            }
        });
    }

    // Tree view button
    if (!options.disableTreeView) {
        buttons.push({
            html: `<button type='button' name='${idx++}' class='btn ${class_tree}' title='{% trans "Display tree view" %}'><span class='fas fa-sitemap'></span></button>`,
            event: function() {
                buttonCallback('tree');
            }
        });
    }

    return buttons;
}


/*
 * Construct buttons to expand / collapse all rows in a table
 */
function constructExpandCollapseButtons(table, idx=0) {

    return [
        {
            html: `<button type='button' name='${idx++}' class='btn btn-outline-secondary' title='{% trans "Expand all rows" %}'><span class='fas fa-expand'></span></button>`,
            event: function() {
                $(table).bootstrapTable('expandAllRows');
            }
        },
        {
            html: `<button type='button' name='${idx++}' class='btn btn-outline-secondary' title='{% trans "Collapse all rows" %}'><span class='fas fa-compress'></span></button>`,
            event: function() {
                $(table).bootstrapTable('collapseAllRows');
            }
        }
    ];
}


/* Return the 'selected' data rows from a bootstrap table.
 * If allowEmpty = false, and the returned dataset is empty,
 * then instead try to return *all* the data
 */
function getTableData(table, allowEmpty=false) {

    let data = $(table).bootstrapTable('getSelections');

    if (data.length == 0 && allowEmpty) {
        data = $(table).bootstrapTable('getData');
    }

    return data;
}


/**
 * Download data from a table, via the API.
 * This requires a number of conditions to be met:
 *
 * - The API endpoint supports data download (on the server side)
 * - The table is "flat" (does not support multi-level loading, etc)
 * - The table has been loaded using the inventreeTable() function, not bootstrapTable()
 *   (Refer to the "reloadTableFilters" function to see why!)
 */
function downloadTableData(table, opts={}) {

    // Extract table configuration options
    var table_options = table.bootstrapTable('getOptions');

    var url = table_options.url;

    if (!url) {
        console.error('downloadTableData could not find "url" parameter.');
    }

    var query_params = table_options.query_params || {};

    url += '?';

    constructFormBody({}, {
        title: opts.title || '{% trans "Export Table Data" %}',
        fields: {
            format: {
                label: '{% trans "Format" %}',
                help_text: '{% trans "Select File Format" %}',
                required: true,
                type: 'choice',
                value: 'csv',
                choices: exportFormatOptions(),
            }
        },
        onSubmit: function(fields, form_options) {
            var format = getFormFieldValue('format', fields['format'], form_options);

            // Hide the modal
            $(form_options.modal).modal('hide');

            for (const [key, value] of Object.entries(query_params)) {
                url += `${key}=${value}&`;
            }

            url += `export=${format}`;

            location.href = url;
        }
    });
}



function enableButtons(elements, enabled) {
    for (let item of elements) {
        $(item).prop('disabled', !enabled);
    }
}


/**
 * Returns true if the input looks like a valid number
 * @param {String} n
 * @returns
 */
function isNumeric(n) {
    return !isNaN(parseFloat(n)) && isFinite(n);
}


/*
 * Reload a table which has already been made into a bootstrap table.
 * New filters can be optionally provided, to change the query params.
 */
function reloadTableFilters(table, filters, options={}) {

    // If a callback is specified, let's use that
    if (options.callback) {
        options.callback(table, filters, options);
        return;
    }

    // Simply perform a refresh
    if (filters == null) {
        table.bootstrapTable('refresh');
        return;
    }

    // More complex refresh with new filters supplied
    options = table.bootstrapTable('getOptions');

    // Construct a new list of filters to use for the query
    let params = Object.assign({}, filters);

    // Original query params will override
    if (options.original) {
        params = Object.assign(params, options.original);
    }

    // Store the total set of query params
    // This is necessary for the "downloadTableData" function to work
    options.query_params = params;

    options.queryParams = function(tableParams) {
        return convertQueryParameters(tableParams, params);
    };

    table.bootstrapTable('refreshOptions', options);
    table.bootstrapTable('refresh', filters);
}


function visibleColumnString(columns) {
    /* Generate a list of "visible" columns to save to file. */

    var fields = [];

    columns.forEach(function(column) {
        if (column.switchable && column.visible) {
            fields.push(column.field);
        }
    });

    return fields.join(',');
}


/*
 * Convert bootstrap-table style parameters to "InvenTree" style
*/
function convertQueryParameters(params, filters) {

    // Override the way that we ask the server to sort results
    // It seems bootstrap-table does not offer a "native" way to do this...
    if ('sort' in params) {
        var order = params['order'];

        var ordering = params['sort'] || null;

        if (ordering) {
            if (order == 'desc') {
                ordering = `-${ordering}`;
            }

            params['ordering'] = ordering;
        }

        delete params['sort'];
        delete params['order'];

    }

    params = Object.assign(params, filters);

    // Add "order" back in (if it was originally specified by InvenTree)
    // Annoyingly, "order" shadows some field names in InvenTree...
    if ('order' in filters) {
        params['order'] = filters['order'];
    }

    // Remove searchable[] array (generated by bootstrap-table)
    if ('searchable' in params) {
        delete params['searchable'];
    }

    if ('sortable' in params) {
        delete params['sortable'];
    }

    // If "original_search" parameter is provided, add it to the "search"
    if ('original_search' in params) {
        var search = params['search'] || '';

        var clean_search = sanitizeInputString(search + ' ' + params['original_search']);

        params['search'] = clean_search;

        delete params['original_search'];
    }

    // Enable regex search
    if (user_settings.SEARCH_REGEX) {
        params['search_regex'] = true;
    }

    // Enable whole word search
    if (user_settings.SEARCH_WHOLE) {
        params['search_whole'] = true;
    }

    return params;
}


/* Wrapper function for bootstrapTable.
 * Sets some useful defaults, and manage persistent settings.
 */
$.fn.inventreeTable = function(options) {

    var table = this;

    var tableName = options.name || 'table';

    var varName = tableName + '-pagesize';

    // Pagingation options (can be server-side or client-side as specified by the caller)
    if (!options.disablePagination) {
        options.pagination = true;
        options.paginationVAlign = options.paginationVAlign || 'both';
        options.pageSize = options.pageSize || inventreeLoad(varName, 25);
        options.pageList = [25, 50, 100, 250, 'all'];
        options.totalField = 'count';
        options.dataField = 'results';

    } else {
        options.pagination = false;
    }

    // Extract query params
    var filters = options.queryParams || options.filters || {};

    options.escape = true;

    // Store the total set of query params
    options.query_params = filters;

    options.queryParams = function(params) {
        // Update the query parameters callback with the *new* filters
        return convertQueryParameters(params, filters);
    };

    options.rememberOrder = true;

    if (options.sortable == null) {
        options.sortable = true;
    }

    if (options.search == null) {
        options.search = true;
    }

    if (options.showColumns == null) {
        options.showColumns = true;
    }

    // Callback to save pagination data
    options.onPageChange = function(number, size) {
        inventreeSave(varName, size);
    };

    // Callback when a column is changed
    options.onColumnSwitch = function() {

        var columns = table.bootstrapTable('getVisibleColumns');

        var text = visibleColumnString(columns);

        // Save visible columns
        inventreeSave(`table_columns_${tableName}`, text);
    };

    // Standard options for all tables
    table.bootstrapTable(options);

    // Load visible column list from memory
    // Load visible column list
    var visibleColumns = inventreeLoad(`table_columns_${tableName}`, null);

    // If a set of visible columns has been saved, load!
    if (visibleColumns) {
        var columns = visibleColumns.split(',');

        // Which columns are currently visible?
        var visible = table.bootstrapTable('getVisibleColumns');

        if (visible && Array.isArray(visible)) {
            visible.forEach(function(column) {

                // Visible field should *not* be visible! (hide it!)
                if (column.switchable && !columns.includes(column.field)) {
                    table.bootstrapTable('hideColumn', column.field);
                }
            });
        } else {
            console.error(`Could not get list of visible columns for table '${tableName}'`);
        }
    }
};


function customGroupSorter(sortName, sortOrder, sortData) {

    var order = sortOrder === 'desc' ? -1 : 1;

    sortData.sort(function(a, b) {

        // Extract default field values
        // Allow multi-level access if required
        // Ref: https://stackoverflow.com/a/6394168

        function extract(obj, i) {
            return obj[i];
        }

        var aa = sortName.split('.').reduce(extract, a);
        var bb = sortName.split('.').reduce(extract, b);

        // Extract parent information
        var apparent = a._data && a._data['parent-index'];
        var bparent = b._data && b._data['parent-index'];

        // If either of the comparisons are in a group
        if (apparent || bparent) {

            // If the parents are different (or one item does not have a parent,
            // then we need to extract the parent value for the selected column.

            if (apparent != bparent) {
                if (apparent) {
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

// Expose default bootstrap table string literals to translation layer
(function($) {
    'use strict';

    $.fn.bootstrapTable.locales['en-US-custom'] = {
        formatLoadingMessage: function() {
            return '{% trans "Loading data" %}';
        },
        formatRecordsPerPage: function(pageNumber) {
            return `${pageNumber} {% trans "rows per page" %}`;
        },
        formatShowingRows: function(pageFrom, pageTo, totalRows) {

            if (totalRows === undefined || isNaN(totalRows)) {
                return '{% trans "Showing all rows" %}';
            } else {
                return `{% trans "Showing" %} ${pageFrom} {% trans "to" %} ${pageTo} {% trans "of" %} ${totalRows} {% trans "rows" %}`;
            }
        },
        formatSearch: function() {
            return '{% trans "Search" %}';
        },
        formatNoMatches: function() {
            return '{% trans "No matching results" %}';
        },
        formatPaginationSwitch: function() {
            return '{% trans "Hide/Show pagination" %}';
        },
        formatRefresh: function() {
            return '{% trans "Refresh" %}';
        },
        formatToggle: function() {
            return '{% trans "Toggle" %}';
        },
        formatColumns: function() {
            return '{% trans "Columns" %}';
        },
        formatAllRows: function() {
            return '{% trans "All" %}';
        },
    };

    $.extend($.fn.bootstrapTable.defaults, $.fn.bootstrapTable.locales['en-US-custom']);

    // Enable HTML escaping by default
    $.fn.bootstrapTable.escape = true;

    // Override the 'calculateObjectValue' function at bootstrap-table.js:3525
    // Allows us to escape any nasty HTML tags which are rendered to the DOM
    $.fn.bootstrapTable.utils._calculateObjectValue = $.fn.bootstrapTable.utils.calculateObjectValue;

    $.fn.bootstrapTable.utils.calculateObjectValue = function escapeCellValue(self, name, args, defaultValue) {

        var args_list = [];

        if (args) {

            args_list.push(args[0]);

            if (name && typeof(name) === 'function' && name.name == 'formatter') {
                /* This is a custom "formatter" function for a particular cell,
                * which may side-step regular HTML escaping, and inject malicious code into the DOM.
                *
                * Here we have access to the 'args' supplied to the custom 'formatter' function,
                * which are in the order:
                * args = [value, row, index, field]
                *
                * 'row' is the one we are interested in
                */

                var row = Object.assign({}, args[1]);

                args_list.push(sanitizeData(row));
            } else {
                args_list.push(args[1]);
            }

            for (var ii = 2; ii < args.length; ii++) {
                args_list.push(args[ii]);
            }
        }

        var value = $.fn.bootstrapTable.utils._calculateObjectValue(self, name, args_list, defaultValue);

        return value;
    };

})(jQuery);

$.extend($.fn.treegrid.defaults, {
    expanderExpandedClass: 'treegrid-expander-expanded',
    expanderCollapsedClass: 'treegrid-expander-collapsed'
});
