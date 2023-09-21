{% load i18n %}

/* globals
    checkPermission,
    downloadTableData,
    getAvailableTableFilters,
    getTableData,
    global_settings,
    inventreeLoad,
    inventreeSave,
    printLabels,
    printReports,
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
function loadTableFilters(tableKey, query={}) {

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

    // Override configurable filters with hard-coded query
    filters = Object.assign(filters, query);
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
    } else if (settings.type == 'date') {
        return 'date';
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
    } else if (options == 'date') {
        html = `<input type='date' class='dateinput form-control filter-input' id='${id}' name='value'></input>`;
    } else {
        // Return a 'select' input with the available values
        html = `<select class='form-control filter-input' id='${id}' name='value'>`;

        // options can be an object or a function, in which case we need to run
        // this callback first
        if (options instanceof Function) {
            options = options();
        }
        for (var key in options) {
            let option = options[key];
            html += `<option value='${option.key || key}'>${option.value}</option>`;
        }

        html += `</select>`;
    }

    return html;
}


/*
 * Construct a single action button based on the provided definition
 */
function makeFilterActionButton(button, options={}) {
    let prefix = options.prefix || 'action';

    // Check for required permission (if specified)
    if (button.permission) {
        if (!checkPermission(button.permission)) {
            return '';
        }
    }

    return `
    <li><a class='dropdown-item' href='#' id='action-${prefix}-${button.label}'>
        <span class='fas ${button.icon}'></span> ${button.title}
    </a></li>`;
}


/*
 * Construct a set of custom actions for a given table
 */
function makeCustomActionGroup(action_group, table) {

    let buttons = [];
    let label = action_group.label || 'actions';
    let title = action_group.title || '{% trans "Actions" %}';
    let icon = action_group.icon || 'fa-tools';

    // Construct the HTML for each button
    action_group.actions.forEach(function(action) {
        buttons.push(makeFilterActionButton(action, {prefix: label}));
    });

    if (buttons.length == 0) {
        // Don't display anything if there are no buttons to show
        return '';
    }

    let html = `
    <div class='btn-group' role='group'>
    <button id='${label}-actions' title='${title}' class='btn btn-outline-secondary dropdown-toggle' type='button' data-bs-toggle='dropdown'>
        <span class='fas ${icon}'></span>
    </button>
    <ul class='dropdown-menu' role='menu'>
    `;

    buttons.forEach(function(button) {
        html += button;
    });

    html += `</ul></div>`;
    return html;
}


/*
 * Construct a set of custom barcode actions for a given table
 *
 * To define barcode actions for a data table, use options.barcode_actions
 */
function makeBarcodeActions(barcode_actions, table) {

    let html = `
    <div class='btn-group' role='group'>
    <button id='barcode-actions' title='{% trans "Barcode actions" %}' class='btn btn-outline-secondary dropdown-toggle' type='button' data-bs-toggle='dropdown'>
        <span class='fas fa-qrcode'></span>
    </button>
    <ul class='dropdown-menu' role='menu'>
    `;

    barcode_actions.forEach(function(action) {
        html += makeFilterActionButton(action, {prefix: 'barcode'});
    });

    html += `</ul></div>`;

    return html;
}


/*
 * Add callbacks for custom actions
 */
function addFilterActionCallbacks(element, label, table, actions) {
    actions.forEach(function(action) {
        let id = `action-${label}-${action.label}`;
        element.find(`#${id}`).click(function() {
            let data = getTableData(table);
            action.callback(data);
        });
    });
}


/*
 * Helper function to make a 'filter' style button
 */
function makeFilterButton(options={}) {

    return `
    <button id='${options.id}' title='${options.title}' class='btn btn-outline-secondary filter-button'>
        <span class='fas ${options.icon}'></span>
    </button>`;
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

    // Construct a set of buttons
    var buttons = '';

    let report_button = options.report && global_settings.REPORT_ENABLE;
    let labels_button = options.labels && global_settings.LABEL_ENABLE;
    let barcode_actions = options.barcode_actions && global_settings.BARCODE_ENABLE;

    // Add in "custom" actions first (to the left of the table buttons)
    if (options.custom_actions) {
        options.custom_actions.forEach(function(action_group) {
            buttons += makeCustomActionGroup(action_group, table);
        });
    }

    // Add in button for custom barcode actions
    if (barcode_actions) {
        buttons += makeBarcodeActions(options.barcode_actions, table);
    }

    if (report_button || labels_button) {
        let print_buttons = `
        <div class='btn-group' role='group'>
        <button id='printing-options' title='{% trans "Printing actions" %}' class='btn btn-outline-secondary dropdown-toggle' type='button' data-bs-toggle='dropdown'>
            <span class='fas fa-print'></span> <span class='caret'></span>
        </button>
        <ul class='dropdown-menu' role='menu'>`;

        if (labels_button) {
            print_buttons += `<li><a class='dropdown-item' href='#' id='print-labels-${tableKey}'><span class='fas fa-tag'></span> {% trans "Print Labels" %}</a></li>`;
        }

        if (report_button) {
            print_buttons += `<li><a class='dropdown-item' href='#' id='print-report-${tableKey}'><span class='fas fa-file-pdf'></span> {% trans "Print Reports" %}</a></li>`;
        }

        print_buttons += `</ul></div>`;

        buttons += print_buttons;
    }

    // Add download button
    if (options.download) {
        buttons += makeFilterButton({
            id: `download-${tableKey}`,
            title: '{% trans "Download table data" %}',
            icon: 'fa-download',
        });
    }

    buttons += makeFilterButton({
        id: `reload-${tableKey}`,
        title: '{% trans "Reload table data" %}',
        icon: 'fa-redo-alt',
    });

    // If there are filters defined for this table, add more buttons
    if (!jQuery.isEmptyObject(getAvailableTableFilters(tableKey))) {

        buttons += makeFilterButton({
            id: add,
            title: '{% trans "Add new filter" %}',
            icon: 'fa-filter',
        });


        if (Object.keys(filters).length > 0) {
            buttons += makeFilterButton({
                id: clear,
                title: '{% trans "Clear all filters" %}',
                icon: 'fa-backspace icon-red',
            });
        }
    }

    element.html(`
    <div class='btn-group filter-group' role='group'>
        ${buttons}
    </div>
    `);

    for (var key in filters) {
        let value = getFilterOptionValue(tableKey, key, filters[key]);
        let title = getFilterTitle(tableKey, key);
        let description = getFilterDescription(tableKey, key);

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

    // Callback for custom actions
    if (options.custom_actions) {
        options.custom_actions.forEach(function(action_group) {
            let label = action_group.label || 'actions';
            addFilterActionCallbacks(element, label, table, action_group.actions);
        });
    }

    // Callback for barcode actions
    if (barcode_actions) {
        addFilterActionCallbacks(element, 'barcode', table, options.barcode_actions);
    }

    // Callback for printing reports
    if (options.report && global_settings.REPORT_ENABLE) {
        element.find(`#print-report-${tableKey}`).click(function() {
            let data = getTableData(table);
            let items = [];

            data.forEach(function(row) {
                items.push(row.pk);
            });

            printReports({
                items: items,
                url: options.report.url,
                key: options.report.key
            });
        });
    }

    // Callback for printing labels
    if (options.labels && global_settings.LABEL_ENABLE) {
        element.find(`#print-labels-${tableKey}`).click(function() {
            let data = getTableData(table);
            let items = [];

            data.forEach(function(row) {
                items.push(row.pk);
            });

            printLabels({
                items: items,
                singular_name: options.singular_name,
                plural_name: options.plural_name,
                url: options.labels.url,
                key: options.labels.key,
            });
        });
    }

    // Callback for reloading the table
    element.find(`#reload-${tableKey}`).click(function() {
        reloadTableFilters(table, null, options);
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
                    reloadTableFilters(table, filters, options);

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

        reloadTableFilters(table, filters, options);
        setupFilterList(tableKey, table, target, options);
    });

    // Add callback for deleting each filter
    element.find('.close').click(function() {
        var me = $(this);

        var filter = me.attr(`filter-tag-${tableKey}`);

        var filters = removeTableFilter(tableKey, filter);

        reloadTableFilters(table, filters, options);

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
        // options can be an object or a function, in which case we need to run
        // this callback first
        if (filter.options instanceof Function) {
            filter.options = filter.options();
        }

        for (var name in filter.options) {
            let option = filter.options[name];

            if (option.key == valueKey) {
                return option.value;
            }
        }

        // Could not find a match
        return value;
    }

    // Cannot map to a display string - return the original text
    return value;
}
