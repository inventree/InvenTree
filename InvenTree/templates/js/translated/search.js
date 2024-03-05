{% load i18n %}

/* globals
    checkPermission,
    getModelRenderer,
    inventreeGet,
    inventreePut,
    sanitizeInputString,
    user_settings,
*/

/* exported
    closeSearchPanel,
    openSearchPanel,
    searchTextChanged,
*/


/*
 * Callback when the search panel is closed
 */
function closeSearchPanel() {
}



/*
 * Callback when the search panel is opened.
 * Ensure the panel is in a known state
 */
function openSearchPanel() {

    var panel = $('#offcanvas-search');

    let search_input = panel.find('#search-input');
    search_input.find('#search-input').val('');
    search_input.focus();

    clearSearchResults();

    // Callback for text input changed
    search_input.on('keyup change', searchTextChanged);

    // Callback for "clear search" button
    panel.find('#search-clear').click(function(event) {

        // Prevent this button from actually submitting the form
        event.preventDefault();

        search_input('#search-input').val('');
        clearSearchResults();
    });

    // Callback for the "close search" button
    panel.find('#search-close').click(function(event) {
        // Prevent this button from actually submitting the form
        event.preventDefault();
    });
}

var searchInputTimer = null;
var searchText = null;
var searchTextCurrent = null;
var searchQuery = null;
var searchResultTypes = [];
var searchRequest = null;


/*
 * Callback for when the search text is changed
 */
function searchTextChanged(event) {

    var text = $('#offcanvas-search').find('#search-input').val();

    searchText = sanitizeInputString(text);

    clearTimeout(searchInputTimer);
    searchInputTimer = setTimeout(updateSearch, 250);
}


/*
 * Update the search results
 */
function updateSearch() {

    if (searchText == searchTextCurrent) {
        return;
    }

    clearSearchResults();

    if (searchText.length == 0) {
        return;
    }

    searchTextCurrent = searchText;

    // Cancel previous search request
    if (searchRequest != null) {
        searchRequest.abort();
        searchRequest = null;
    }

    // Show the "searching" text
    $('#offcanvas-search').find('#search-pending').show();

    searchResultTypes = [];

    // Construct base query
    searchQuery = {
        search: searchTextCurrent,
        search_regex: user_settings.SEARCH_REGEX ? true : false,
        search_whole: user_settings.SEARCH_WHOLE ? true : false,
        limit: user_settings.SEARCH_PREVIEW_RESULTS,
        offset: 0,
    };

    // Search for 'part' results
    if (checkPermission('part') && user_settings.SEARCH_PREVIEW_SHOW_PARTS) {

        let filters = {};

        if (user_settings.SEARCH_HIDE_INACTIVE_PARTS) {
            // Return *only* active parts
            filters.active = true;
        }

        addSearchQuery('part', '{% trans "Parts" %}', filters);
    }

    if (checkPermission('part') && checkPermission('purchase_order')) {

        let filters = {
            part_detail: true,
            supplier_detail: true,
            manufacturer_detail: true,
        };

        if (user_settings.SEARCH_HIDE_INACTIVE_PARTS) {
            // Return *only* active parts
            filters.active = true;
        }

        if (user_settings.SEARCH_PREVIEW_SHOW_SUPPLIER_PARTS) {
            addSearchQuery('supplierpart', '{% trans "Supplier Parts" %}', filters);
        }

        if (user_settings.SEARCH_PREVIEW_SHOW_MANUFACTURER_PARTS) {
            addSearchQuery('manufacturerpart', '{% trans "Manufacturer Parts" %}', filters);
        }
    }

    if (checkPermission('part_category') && user_settings.SEARCH_PREVIEW_SHOW_CATEGORIES) {
        let filters = {};

        addSearchQuery('partcategory', '{% trans "Part Categories" %}', filters);
    }

    if (checkPermission('stock') && user_settings.SEARCH_PREVIEW_SHOW_STOCK) {
        let filters = {
            part_detail: true,
            location_detail: true,
        };

        if (user_settings.SEARCH_PREVIEW_HIDE_UNAVAILABLE_STOCK) {
            // Only show 'in stock' items in the preview windoww
            filters.in_stock = true;
        }

        addSearchQuery('stockitem', '{% trans "Stock Items" %}', filters);
    }

    if (checkPermission('stock_location') && user_settings.SEARCH_PREVIEW_SHOW_LOCATIONS) {
        let filters = {};

        addSearchQuery('stocklocation', '{% trans "Stock Locations" %}', filters);
    }

    if (checkPermission('build') && user_settings.SEARCH_PREVIEW_SHOW_BUILD_ORDERS) {
        let filters = {
            part_detail: true
        };

        addSearchQuery('build', '{% trans "Build Orders" %}', filters);
    }

    if ((checkPermission('sales_order') || checkPermission('purchase_order')) && user_settings.SEARCH_PREVIEW_SHOW_COMPANIES) {
        let filters = {};

        addSearchQuery('company', '{% trans "Companies" %}', filters);
    }

    if (checkPermission('purchase_order') && user_settings.SEARCH_PREVIEW_SHOW_PURCHASE_ORDERS) {

        let filters = {
            supplier_detail: true,
        };

        if (user_settings.SEARCH_PREVIEW_EXCLUDE_INACTIVE_PURCHASE_ORDERS) {
            filters.outstanding = true;
        }

        addSearchQuery('purchaseorder', '{% trans "Purchase Orders" %}', filters);
    }

    if (checkPermission('sales_order') && user_settings.SEARCH_PREVIEW_SHOW_SALES_ORDERS) {

        let filters = {
            customer_detail: true,
        };

        // Hide inactive (not "outstanding" orders)
        if (user_settings.SEARCH_PREVIEW_EXCLUDE_INACTIVE_SALES_ORDERS) {
            filters.outstanding = true;
        }

        addSearchQuery('salesorder', '{% trans "Sales Orders" %}', filters);
    }

    if (checkPermission('return_order') && user_settings.SEARCH_PREVIEW_SHOW_RETURN_ORDERS) {
        let filters = {
            customer_detail: true,
        };

        // Hide inactive (not "outstanding" orders)
        if (user_settings.SEARCH_PREVIEW_EXCLUDE_INACTIVE_RETURN_ORDERS) {
            filters.outstanding = true;
        }

        addSearchQuery('returnorder', '{% trans "Return Orders" %}', filters);
    }

    let ctx = $('#offcanvas-search').find('#search-context');

    ctx.html(`
    <div class='alert alert-block alert-secondary'>
        <span class='fas fa-spinner fa-spin'></span> <em>{% trans "Searching" %}</em>
    </div>
    `);

    // Send off the search query
    searchRequest = inventreePut(
        '{% url "api-search" %}',
        searchQuery,
        {
            method: 'POST',
            success: function(response) {

                let any_results = false;

                searchResultTypes.forEach(function(resultType) {
                    if (resultType.key in response) {
                        let result = response[resultType.key];

                        if (result.count != null && result.count > 0 && result.results) {
                            addSearchResults(result.results, resultType, result.count);

                            any_results = true;
                        }
                    }
                });

                if (any_results) {
                    ctx.html('');
                } else {
                    ctx.html(`
                    <div class='alert alert-block alert-warning'>
                        <span class='fas fa-exclamation-circle'></span> <em>{% trans "No results" %}</em>
                    </div>
                    `);
                }
            },
            complete: function() {
                // Hide the "pending" icon
                $('#offcanvas-search').find('#search-pending').hide();
            }
        }
    );
}


function clearSearchResults() {

    var panel = $('#offcanvas-search');

    panel.find('#search-pending').hide();

    panel.find('#search-context').html(`
    <div class='alert alert-block alert-info'>
        <span class='fas fa-search'></span> <em>{% trans "Enter search query" %}</em>
    </div>
    `);

    // Delete any existing search results
    panel.find('#search-results').empty();

    // Finally, grab keyboard focus in the search bar
    panel.find('#search-input').focus();
}


/*
 * Add an individual search query, with callback for rendering
 */
function addSearchQuery(key, title, query_params, render_params={}) {

    searchQuery[key] = query_params;

    render_params.showImage = true;
    render_params.showLink = true;
    render_params.showLabels = true;

    searchResultTypes.push({
        key: key,
        title: title,
        renderer: getModelRenderer(key),
        renderParams: render_params,
    });
}


// Add a group of results to the list
function addSearchResults(results, resultType, resultCount) {

    if (results.length == 0) {
        // Do not display this group, as there are no results
        return;
    }

    let panel = $('#offcanvas-search');

    // Ensure the 'no results found' element is hidden
    panel.find('#search-no-results').hide();

    let key = resultType.key;
    let title = resultType.title;
    let renderer = resultType.renderer;
    let renderParams = resultType.renderParams;

    let resultText = resultCount == 1 ? '{% trans "result" %}' : '{% trans "results" %}';

    // Add the result group to the panel
    panel.find('#search-results').append(`
    <div class='search-result-group-wrapper' id='search-results-wrapper-${key}'>
        <div class='search-result-group' id='search-results-${key}'>
            <div class='search-result-header' style='display: flex;'>
                <h5>${title}</h5><span class='float-right'><em><small>&nbsp;-&nbsp;${resultCount} ${resultText}</small></em></span>
                <span class='flex' style='flex-grow: 1;'></span>
                <div class='search-result-group-buttons btn-group float-right' role='group'>
                    <button class='btn btn-outline-secondary' id='hide-results-${key}' title='{% trans "Minimize results" %}'>
                        <span class='fas fa-chevron-up'></span>
                    </button>
                    <button class='btn btn-outline-secondary' id='remove-results-${key}' title='{% trans "Remove results" %}'>
                        <span class='fas fa-times icon-red'></span>
                    </button>
                </div>
            </div>
            <div class='collapse search-result-list' id='search-result-list-${key}'>
            </div>
        </div>
    </div>
    `);

    results.forEach(function(result) {

        var pk = result.pk || result.id;

        var html = renderer(result, renderParams);

        var result_html = `
        <div class='search-result-entry' id='search-result-${key}-${pk}'>
            ${html}
        </div>
        `;

        panel.find(`#search-result-list-${key}`).append(result_html);
    });

    // Expand results panel
    panel.find(`#search-result-list-${key}`).toggle();

    // Add callback for "toggle" button
    panel.find(`#hide-results-${key}`).click(function() {
        panel.find(`#search-result-list-${key}`).toggle();
    });

    // Add callback for "remove" button
    panel.find(`#remove-results-${key}`).click(function() {
        panel.find(`#search-results-${key}`).remove();
    });
}
