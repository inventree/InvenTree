{% load i18n %}

/* globals
    getAvailableTableFilters,
    inventreeLoad,
    inventreeSave,
    reloadTableFilters,
*/

/* exported
   setupFilterList,
*/

/**
 * Code for managing query filters / table options.
 *
 * Optional query filters are available to the user for various
 * tables display in the web interface.
 * These filters are saved to the web session, and should be
 * persistent for a given table type.
 *
 * This makes use of the 'inventreeSave' and 'inventreeLoad' functions
 * for writing to and reading from session storage.
 *
 */


function defaultFilters() {
    return {
        stock: 'cascade=1&in_stock=1',
        build: '',
        parts: 'cascade=1',
        company: '',
        salesorder: '',
        purchaseorder: '',
    };
}


/**
 * Load table filters for the given table from session storage
 *
 * @param tableKey - String key for the particular table
 * @param defaults - Default filters for this table e.g. 'cascade=1&location=5'
 */
function loadTableFilters(tableKey) {

    var lookup = 'table-filters-' + tableKey.toLowerCase();

    var defaults = defaultFilters()[tableKey] || '';

    var filterstring = inventreeLoad(lookup, defaults);

    var filters = {};

    filterstring.split('&').forEach(function(item) {
        item = item.trim();

        if (item.length > 0) {
            var f = item.split('=');

            if (f.length == 2) {
                filters[f[0]] = f[1];
            } else {
                console.warn(`Improperly formatted filter: ${item}`);
            }
        }
    });

    return filters;
}


/**
 * Save table filters to session storage
 *
 * @param {*} tableKey - string key for the given table
 * @param {*} filters - object of string:string pairs
 */
function saveTableFilters(tableKey, filters) {
    var lookup = 'table-filters-' + tableKey.toLowerCase();

    var strings = [];

    for (var key in filters) {
        strings.push(`${key.trim()}=${String(filters[key]).trim()}`);
    }

    var filterstring = strings.join('&');

    inventreeSave(lookup, filterstring);
}


/*
 * Remove a named filter parameter
 */
function removeTableFilter(tableKey, filterKey) {

    var filters = loadTableFilters(tableKey);

    delete filters[filterKey];

    saveTableFilters(tableKey, filters);

    // Return a copy of the updated filters
    return filters;
}


function addTableFilter(tableKey, filterKey, filterValue) {

    var filters = loadTableFilters(tableKey);

    filters[filterKey] = filterValue;

    saveTableFilters(tableKey, filters);

    // Return a copy of the updated filters
    return filters;
}


/*
 * Clear all the custom filters for a given table
 */
function clearTableFilters(tableKey) {
    saveTableFilters(tableKey, {});

    return {};
}


/*
 * Return a list of the "available" filters for a given table key.
 * A filter is "available" if it is not already being used to filter the table.
 * Once a filter is selected, it will not be returned here.
 */
function getRemainingTableFilters(tableKey) {

    var filters = loadTableFilters(tableKey);

    var remaining = getAvailableTableFilters(tableKey);

    for (var key in filters) {
        // Delete the filter if it is already in use
        delete remaining[key];
    }

    return remaining;
}



/*
 * Return the filter settings for a given table and key combination.
 * Return empty object if the combination does not exist.
 */
function getFilterSettings(tableKey, filterKey) {

    return getAvailableTableFilters(tableKey)[filterKey] || {};
}


/*
 * Return a set of key:value options for the given filter.
 * If no options are specified (e.g. for a number field),
 * then a null object is returned.
 */
function getFilterOptionList(tableKey, filterKey) {

    var settings = getFilterSettings(tableKey, filterKey);

    if (settings.type == 'bool') {
        return {
            '1': {
                key: '1',
                value: '{% trans "true" %}',
            },
            '0': {
                key: '0',
                value: '{% trans "false" %}',
            },
        };
    } else if ('options' in settings) {
        return settings.options;
    }

    return null;
}


/*
 * Generate a list of <option> tags for the given table.
 */
function generateAvailableFilterList(tableKey) {

    var remaining = getRemainingTableFilters(tableKey);

    var id = 'filter-tag-' + tableKey.toLowerCase();

    var html = `<select class='form-control filter-input' id='${id}' name='tag'>`;

    html += `<option value=''>{% trans 'Select filter' %}</option>`;

    for (var opt in remaining) {
        var title = getFilterTitle(tableKey, opt);
        html += `<option value='${opt}'>${title}</option>`;
    }

    html += `</select>`;

    return html;
}


/*
 * Generate an input for setting the value of a given filter.
 */
function generateFilterInput(tableKey, filterKey) {

    var id = 'filter-value-' + tableKey.toLowerCase();

    if (filterKey == null || filterKey.length == 0) {
        // Return an 'empty' element
        return `<div class='filter-input' id='${id}'></div>`;
    }

    var options = getFilterOptionList(tableKey, filterKey);

    var html = '';

    // A 'null' options list means that a simple text-input dialog should be used
    if (options == null) {
        html = `<input class='form-control filter-input' id='${id}' name='value'></input>`;
    } else {
        // Return a 'select' input with the available values
        html = `<select class='form-control filter-input' id='${id}' name='value'>`;

        for (var key in options) {
            var option = options[key];
            html += `<option value='${key}'>${option.value}</option>`;
        }

        html += `</select>`;
    }

    return html;
}


/**
 * Configure a filter list for a given table
 *
 * @param {*} tableKey - string lookup key for filter settings
 * @param {*} table - bootstrapTable element to update
 * @param {*} target - name of target element on page
 */
function setupFilterList(tableKey, table, target, options={}) {

    var addClicked = false;

    if (target == null || target.length == 0) {
        target = `#filter-list-${tableKey}`;
    }

    var tag = `filter-tag-${tableKey}`;
    var add = `filter-add-${tableKey}`;
    var clear = `filter-clear-${tableKey}`;
    var make = `filter-make-${tableKey}`;

    var filters = loadTableFilters(tableKey);

    var element = $(target);

    if (!element || !element.exists()) {
        console.warn(`setupFilterList could not find target '${target}'`);
        return;
    }

    // One blank slate, please
    element.empty();

    var buttons = '';

    // Add download button
    if (options.download) {
        buttons += `<button id='download-${tableKey}' title='{% trans "Download data" %}' class='btn btn-outline-secondary filter-button'><span class='fas fa-download'></span></button>`;
    }

    buttons += `<button id='reload-${tableKey}' title='{% trans "Reload data" %}' class='btn btn-outline-secondary filter-button'><span class='fas fa-redo-alt'></span></button>`;

    // If there are filters defined for this table, add more buttons
    if (!jQuery.isEmptyObject(getAvailableTableFilters(tableKey))) {
        buttons += `<button id='${add}' title='{% trans "Add new filter" %}' class='btn btn-outline-secondary filter-button'><span class='fas fa-filter'></span></button>`;

        if (Object.keys(filters).length > 0) {
            buttons += `<button id='${clear}' title='{% trans "Clear all filters" %}' class='btn btn-outline-secondary filter-button'><span class='fas fa-backspace icon-red'></span></button>`;
        }
    }

    element.html(`
    <div class='btn-group filter-group' role='group'>
        ${buttons}
    </div>
    `);

    for (var key in filters) {
        var value = getFilterOptionValue(tableKey, key, filters[key]);
        var title = getFilterTitle(tableKey, key);
        var description = getFilterDescription(tableKey, key);

        var filter_tag = `
        <div title='${description}' class='filter-tag'>
            ${title} = ${value}
            <span ${tag}='${key}' class='close' style='color: #F55;'>
                <span aria-hidden='true'><strong>&times;</strong></span>
            </span>
        </div>
        `;

        element.append(filter_tag);
    }

    // Callback for reloading the table
    element.find(`#reload-${tableKey}`).click(function() {
        $(table).bootstrapTable('refresh');
    });

    // Add a callback for downloading table data
    if (options.download) {
        element.find(`#download-${tableKey}`).click(function() {
            downloadTableData($(table));
        });
    }

    // Add a callback for adding a new filter
    element.find(`#${add}`).click(function clicked() {

        if (!addClicked) {

            addClicked = true;

            var html = '';

            html += `<div class='input-group'>`;
            html += generateAvailableFilterList(tableKey);
            html += generateFilterInput(tableKey);

            html += `<button title='{% trans "Create filter" %}' class='btn btn-outline-secondary filter-button' id='${make}'><span class='fas fa-plus'></span></button>`;
            html += `</div>`;

            element.append(html);

            // Add a callback for when the filter tag selection is changed
            element.find(`#filter-tag-${tableKey}`).on('change', function() {
                var list = element.find(`#filter-value-${tableKey}`);

                list.replaceWith(generateFilterInput(tableKey, this.value));
            });

            // Add a callback for when the new filter is created
            element.find(`#filter-make-${tableKey}`).click(function() {
                var tag = element.find(`#filter-tag-${tableKey}`).val();
                var val = element.find(`#filter-value-${tableKey}`).val();

                // Only add the new filter if it is not empty!
                if (tag && tag.length > 0) {
                    var filters = addTableFilter(tableKey, tag, val);
                    reloadTableFilters(table, filters);

                    // Run this function again
                    setupFilterList(tableKey, table, target, options);
                }

            });
        } else {
            addClicked = false;

            setupFilterList(tableKey, table, target, options);
        }

    });

    // Add a callback for clearing all the filters
    element.find(`#${clear}`).click(function() {
        var filters = clearTableFilters(tableKey);

        reloadTableFilters(table, filters);

        setupFilterList(tableKey, table, target, options);
    });

    // Add callback for deleting each filter
    element.find('.close').click(function() {
        var me = $(this);

        var filter = me.attr(`filter-tag-${tableKey}`);

        var filters = removeTableFilter(tableKey, filter);

        reloadTableFilters(table, filters);

        // Run this function again!
        setupFilterList(tableKey, table, target, options);
    });
}


/**
 * Return the pretty title for the given table and filter selection.
 * If no title is provided, default to the key value.
 *
 */
function getFilterTitle(tableKey, filterKey) {
    var settings = getFilterSettings(tableKey, filterKey);
    return settings.title || filterKey;
}


/*
 * Return a description for the given table and filter selection.
 */
function getFilterDescription(tableKey, filterKey) {
    var settings = getFilterSettings(tableKey, filterKey);
    return settings.description || filterKey;
}


/*
 * Return the display value for a particular option
 */
function getFilterOptionValue(tableKey, filterKey, valueKey) {

    var filter = getFilterSettings(tableKey, filterKey);

    var value = String(valueKey);

    // Lookup for boolean options
    if (filter.type == 'bool') {
        if (value == '1') return '{% trans "true" %}';
        if (value == '0') return '{% trans "false" %}';

        return value;
    }

    // Iterate through a list of options
    if ('options' in filter) {
        for (var key in filter.options) {

            if (key == valueKey) {
                return filter.options[key].value;
            }
        }

        // Could not find a match
        return value;
    }

    // Cannot map to a display string - return the original text
    return value;
}
