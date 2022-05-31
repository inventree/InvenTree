{% load i18n %}

/* globals
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


// Keep track of the roles / permissions available to the current user
var search_user_roles = null;


/*
 * Check if the user has the specified role and permission
 */
function checkPermission(role, permission='view') {

    if (!search_user_roles) {
        return false;
    }

    if (!(role in search_user_roles)) {
        return false;
    }

    var roles = search_user_roles[role];

    if (!roles) {
        return false;
    }

    var found = false;

    search_user_roles[role].forEach(function(p) {
        if (String(p).valueOf() == String(permission).valueOf()) {
            found = true;
        }
    });

    return found;
}


/*
 * Callback when the search panel is opened.
 * Ensure the panel is in a known state
 */
function openSearchPanel() {

    var panel = $('#offcanvas-search');

    clearSearchResults();

    // Request user roles if we do not have them
    if (search_user_roles == null) {
        inventreeGet('{% url "api-user-roles" %}', {}, {
            success: function(response) {
                search_user_roles = response.roles || {};
            }
        });
    }

    // Callback for text input changed
    panel.find('#search-input').on('keyup change', searchTextChanged);

    // Callback for "clear search" button
    panel.find('#search-clear').click(function(event) {

        // Prevent this button from actually submitting the form
        event.preventDefault();

        panel.find('#search-input').val('');
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
var searchQueries = [];

function searchTextChanged(event) {

    searchText = $('#offcanvas-search').find('#search-input').val();

    clearTimeout(searchInputTimer);
    searchInputTimer = setTimeout(updateSearch, 250);
};


function updateSearch() {

    if (searchText == searchTextCurrent) {
        return;
    }

    clearSearchResults();

    if (searchText.length == 0) {
        return;
    }

    searchTextCurrent = searchText;

    // Cancel any previous AJAX requests
    searchQueries.forEach(function(query) {
        query.abort();
    });

    searchQueries = [];

    // Show the "searching" text
    $('#offcanvas-search').find('#search-pending').show();

    if (checkPermission('part') && user_settings.SEARCH_PREVIEW_SHOW_PARTS) {

        var params = {};

        if (user_settings.SEARCH_HIDE_INACTIVE_PARTS) {
            // Return *only* active parts
            params.active = true;
        }

        // Search for matching parts
        addSearchQuery(
            'part',
            '{% trans "Parts" %}',
            '{% url "api-part-list" %}',
            params,
            renderPart,
            {
                url: '/part',
            }
        );
    }

    if (checkPermission('part') && checkPermission('purchase_order')) {

        var params = {
            part_detail: true,
            supplier_detail: true,
            manufacturer_detail: true,
        };

        if (user_settings.SEARCH_HIDE_INACTIVE_PARTS) {
            // Return *only* active parts
            params.active = true;
        }

        if (user_settings.SEARCH_PREVIEW_SHOW_SUPPLIER_PARTS) {
            addSearchQuery(
                'supplierpart',
                '{% trans "Supplier Parts" %}',
                '{% url "api-supplier-part-list" %}',
                params,
                renderSupplierPart,
                {
                    url: '/supplier-part',
                }
            );
        }

        if (user_settings.SEARCH_PREVIEW_SHOW_MANUFACTURER_PARTS) {
            addSearchQuery(
                'manufacturerpart',
                '{% trans "Manufacturer Parts" %}',
                '{% url "api-manufacturer-part-list" %}',
                params,
                renderManufacturerPart,
                {
                    url: '/manufacturer-part',
                }
            );
        }
    }
    
    if (checkPermission('part_category') && user_settings.SEARCH_PREVIEW_SHOW_CATEGORIES) {
        // Search for matching part categories
        addSearchQuery(
            'category',
            '{% trans "Part Categories" %}',
            '{% url "api-part-category-list" %}',
            {},
            renderPartCategory,
            {
                url: '/part/category',
            },
        );
    }

    if (checkPermission('stock') && user_settings.SEARCH_PREVIEW_SHOW_STOCK) {
        // Search for matching stock items

        var filters = {
            part_detail: true,
            location_detail: true,
        };

        if (user_settings.SEARCH_PREVIEW_HIDE_UNAVAILABLE_STOCK) {
            // Only show 'in stock' items in the preview windoww
            filters.in_stock = true;
        }

        addSearchQuery(
            'stock',
            '{% trans "Stock Items" %}',
            '{% url "api-stock-list" %}',
            filters,
            renderStockItem,
            {
                url: '/stock/item',
                render_location_detail: true,
            }
        );
    }

    if (checkPermission('stock_location') && user_settings.SEARCH_PREVIEW_SHOW_LOCATIONS) {
        // Search for matching stock locations
        addSearchQuery(
            'location',
            '{% trans "Stock Locations" %}',
            '{% url "api-location-list" %}',
            {},
            renderStockLocation,
            {
                url: '/stock/location',
            }
        );
    }

    if ((checkPermission('sales_order') || checkPermission('purchase_order')) && user_settings.SEARCH_PREVIEW_SHOW_COMPANIES) {
        // Search for matching companies
        addSearchQuery(
            'company',
            '{% trans "Companies" %}',
            '{% url "api-company-list" %}',
            {},
            renderCompany,
            {
                url: '/company',
            }
        );
    }

    if (checkPermission('purchase_order') && user_settings.SEARCH_PREVIEW_SHOW_PURCHASE_ORDERS) {

        var filters = {
            supplier_detail: true,
        };

        if (user_settings.SEARCH_PREVIEW_EXCLUDE_INACTIVE_PURCHASE_ORDERS) {
            filters.outstanding = true;
        }

        // Search for matching purchase orders
        addSearchQuery(
            'purchaseorder',
            '{% trans "Purchase Orders" %}',
            '{% url "api-po-list" %}',
            filters,
            renderPurchaseOrder,
            {
                url: '/order/purchase-order',
            }
        );
    }

    if (checkPermission('sales_order') && user_settings.SEARCH_PREVIEW_SHOW_SALES_ORDERS) {

        var filters = {
            customer_detail: true,
        };

        // Hide inactive (not "outstanding" orders)
        if (user_settings.SEARCH_PREVIEW_EXCLUDE_INACTIVE_SALES_ORDERS) {
            filters.outstanding = true;
        }

        // Search for matching sales orders
        addSearchQuery(
            'salesorder',
            '{% trans "Sales Orders" %}',
            '{% url "api-so-list" %}',
            filters,
            renderSalesOrder,
            {
                url: '/order/sales-order',
            }
        );
    }

    // Wait until all the pending queries are completed
    $.when.apply($, searchQueries).done(function() {
        $('#offcanvas-search').find('#search-pending').hide();
    });
}


function clearSearchResults() {

    var panel = $('#offcanvas-search');

    // Ensure the 'no results found' element is visible
    panel.find('#search-no-results').show();

    // Ensure that the 'searching' element is hidden
    panel.find('#search-pending').hide();

    // Delete any existing search results
    panel.find('#search-results').empty();

    // Finally, grab keyboard focus in the search bar
    panel.find('#search-input').focus();
}


function addSearchQuery(key, title, query_url, query_params, render_func, render_params={}) {

    // Include current search term
    query_params.search = searchTextCurrent;

    // How many results to show in each group?
    query_params.offset = 0;
    query_params.limit = user_settings.SEARCH_PREVIEW_RESULTS;

    // Do not display "pk" value for search results
    render_params.render_pk = false;

    // Add the result group to the panel
    $('#offcanvas-search').find('#search-results').append(`
    <div class='search-result-group-wrapper' id='search-results-wrapper-${key}'></div>
    `);

    var request = inventreeGet(
        query_url,
        query_params,
        {
            success: function(response) {
                addSearchResults(
                    key,
                    response.results,
                    title,
                    render_func,
                    render_params,
                );
            }
        },
    );

    // Add the query to the stack
    searchQueries.push(request);

}


// Add a group of results to the list
function addSearchResults(key, results, title, renderFunc, renderParams={}) {

    if (results.length == 0) {
        // Do not display this group, as there are no results
        return;
    }

    var panel = $('#offcanvas-search');

    // Ensure the 'no results found' element is hidden
    panel.find('#search-no-results').hide();

    panel.find(`#search-results-wrapper-${key}`).append(`
        <div class='search-result-group' id='search-results-${key}'>
            <div class='search-result-header' style='display: flex;'>
                <h5>${title}</h5>
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
    `);

    results.forEach(function(result) {

        var pk = result.pk || result.id;

        var html = renderFunc(key, result, renderParams);

        if (renderParams.url) {
            html = `<a href='${renderParams.url}/${pk}/'>` + html + `</a>`;
        }

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
