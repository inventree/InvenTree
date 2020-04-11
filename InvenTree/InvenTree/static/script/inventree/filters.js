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


/**
 * Return the custom filtering options available for a particular table
 * 
 * @param {*} tableKey - string key lookup for the table
 */
function getAvailableTableFilters(tableKey) {

    tableKey = tableKey.toLowerCase();

    // Filters for the "Stock" table
    if (tableKey == 'stock') {
        return {
            'cascade': {
                'type': 'bool',
                'description': 'Include stock in sublocations',
                'title': 'sublocations',
            },
            'active': {
                'type': 'bool',
                'title': 'part active',
                'description': 'Show stock for active parts',
            },
            'status': {
                'options': {
                    'OK': 10,
                    'ATTENTION': 50,
                    'DAMAGED': 55,
                    'DESTROYED': 60,
                    'LOST': 70
                },
                'description': 'Stock status',
            }
        };
    }


    // Finally, no matching key
    return {};
}


/*
 * Return a list of the "available" filters for a given table key.
 * A filter is "available" if it is not already being used to filter the table.
 * Once a filter is selected, it will not be returned here.
 */
function getRemainingTableFilters(tableKey) {

    var filters = loadTableFilters(tableKey, '');

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
            'true': '1',
            'false': '0',
        };
    } else if ('options' in settings) {
        return settings.options;
    }

    return null;
}


/**
 * Load table filters for the given table from session storage
 * 
 * @param tableKey - String key for the particular table
 * @param defaults - Default filters for this table e.g. 'cascade=1&location=5'
 */
function loadTableFilters(tableKey, defaults) {

    var lookup = "table-filters-" + tableKey.toLowerCase();

    var filterstring = inventreeLoad(lookup, defaults);

    var filters = {};

    console.log(`Loaded filters for table '${tableKey}' - ${filterstring}`);

    filterstring.split("&").forEach(function(item, index) {
        item = item.trim();

        if (item.length > 0) {
            var f = item.split('=');

            if (f.length == 2) {
                filters[f[0]] = f[1];
            } else {
                console.log(`Improperly formatted filter: ${item}`);
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
    var lookup = "table-filters-" + tableKey.toLowerCase();

    var strings = [];

    for (var key in filters) {
        strings.push(`${key.trim()}=${String(filters[key]).trim()}`);
    }

    var filterstring = strings.join('&');

    console.log(`Saving filters for table '${tableKey}' - ${filterstring}`);

    inventreeSave(lookup, filterstring);
}


/*
 * Remove a named filter parameter
 */
function removeTableFilter(tableKey, filterKey) {

    var filters = loadTableFilters(tableKey, '');

    delete filters[filterKey];

    saveTableFilters(tableKey, filters);

    // Return a copy of the updated filters
    return filters;
}


function addTableFilter(tableKey, filterKey, filterValue) {

    var filters = loadTableFilters(tableKey, '');

    filters[filterKey] = filterValue;

    saveTableFilters(tableKey, filters);

    // Return a copy of the updated filters
    return filters;
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

    var filter = getFilterOption(tableKey, filterKey);

    var value = String(valueKey);

    // Lookup for boolean options
    if (filter.type == 'bool') {
        if (value == '1') return 'true';
        if (value == '0') return 'false';

        return value;
    }

    // Iterate through a list of options
    if ('options' in filter) {
        for (var option in filter.options) {
            var v = String(filter.options[option]);

            if (v == valueKey) {
                return option;
            }
        }

        // Could not find a match
        return value;
    }

    // Cannot map to a display string - return the original text
    return value;
}

