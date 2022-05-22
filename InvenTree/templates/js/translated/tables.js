{% load i18n %}

/* global
    inventreeLoad,
    inventreeSave,
*/

/* exported
    customGroupSorter,
    downloadTableData,
    reloadtable,
    renderLink,
    reloadTableFilters,
*/

/**
 * Reload a named table
 * @param table
 */
function reloadtable(table) {
    $(table).bootstrapTable('refresh');
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




/**
 * Render a URL for display
 * @param {String} text
 * @param {String} url
 * @param {object} options
 * @returns link text
 */
function renderLink(text, url, options={}) {
    if (url === null || url === undefined || url === '') {
        return text;
    }

    var max_length = options.max_length || -1;

    // Shorten the displayed length if required
    if ((max_length > 0) && (text.length > max_length)) {
        var slice_length = (max_length - 3) / 2;

        var text_start = text.slice(0, slice_length);
        var text_end = text.slice(-slice_length);

        text = `${text_start}...${text_end}`;
    }

    return '<a href="' + url + '">' + text + '</a>';
}


function enableButtons(elements, enabled) {
    for (let item of elements) {
        $(item).prop('disabled', !enabled);
    }
}


/* Link a bootstrap-table object to one or more buttons.
 * The buttons will only be enabled if there is at least one row selected
 */
function linkButtonsToSelection(table, buttons) {

    if (typeof table === 'string') {
        table = $(table);
    }

    // Initially set the enable state of the buttons
    enableButtons(buttons, table.bootstrapTable('getSelections').length > 0);

    // Add a callback
    table.on('check.bs.table uncheck.bs.table check-some.bs.table uncheck-some.bs.table check-all.bs.table uncheck-all.bs.table', function() {
        enableButtons(buttons, table.bootstrapTable('getSelections').length > 0);
    });
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
function reloadTableFilters(table, filters) {

    // Simply perform a refresh
    if (filters == null) {
        table.bootstrapTable('refresh');
        return;
    }

    // More complex refresh with new filters supplied
    var options = table.bootstrapTable('getOptions');

    // Construct a new list of filters to use for the query
    var params = {};

    for (var k in filters) {
        params[k] = filters[k];
    }

    // Original query params will override
    if (options.original != null) {
        for (var key in options.original) {
            params[key] = options.original[key];
        }
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

    for (var key in filters) {
        params[key] = filters[key];
    }

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

        params['search'] = search + ' ' + params['original_search'];

        delete params['original_search'];
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

    // Optionally, link buttons to the table selection
    if (options.buttons) {
        linkButtonsToSelection(table, options.buttons);
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

            if (totalRows === undefined || totalRows === NaN) {
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

})(jQuery);

$.extend($.fn.treegrid.defaults, {
    expanderExpandedClass: 'treegrid-expander-expanded',
    expanderCollapsedClass: 'treegrid-expander-collapsed'
});
