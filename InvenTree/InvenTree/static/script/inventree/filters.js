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
function getFilterOptions(tableKey) {

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