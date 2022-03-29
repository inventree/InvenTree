{% load i18n %}

/* globals
*/

/* exported
    closeSearchPanel,
    openSearchPanel,
    searchTextChanged,
*/


function closeSearchPanel() {

    // TODO
    
}


/*
 * Callback when the search panel is opened.
 * Ensure the panel is in a known state
 */
function openSearchPanel() {

    var panel = $('#offcanvas-search');

    clearSearchResults();

    // Finally, grab keyboard focus in the search bar
    panel.find('#search-input').focus();

    panel.find('#search-input').on('keyup change', searchTextChanged);

    // Callback for "clear search" button
    panel.find('#search-clear').click(function() {
        panel.find('#search-input').val('');
        clearSearchResults();
    });
}

var searchRequests = [];
var searchInputTimer = null;
var searchText = null;
var searchTextPrevious = null;
var searchQueries = [];

function searchTextChanged(event) {

    searchText = $('#offcanvas-search').find('#search-input').val();

    clearTimeout(searchInputTimer);
    searchInputTimer = setTimeout(updateSearch, 250);
};


function updateSearch() {

    if (searchText == searchTextPrevious) {
        return;
    }

    clearSearchResults();
    
    if (searchText.length == 0) {
        return;
    }
    
    searchTextPrevious = searchText;

    // Cancel any previous AJAX requests
    searchQueries.forEach(function(query) {
        query.abort();
    });

    searchQueries = [];
    
    // Search for matching parts
    searchQueries.push(inventreeGet(
        `{% url "api-part-list" %}`,
        {
            search: searchText,
            limit: 10,
            offset: 0,
        },
        {
            success: function(response) {
                addSearchResults(
                    'part',
                    response.results,
                    '{% trans "Parts" %}',
                    renderPart,
                    {
                        show_stock_data: false,
                        url: '/part',
                    }
                );
            }
        }
    ));

    // Search for matching stock items
    searchQueries.push(inventreeGet(
        '{% url "api-stock-list" %}',
        {
            search: searchText,
            limit: 10,
            offset: 0,
            part_detail: true,
            location_detail: true,
        },
        {
            success: function(response) {
                addSearchResults(
                    'stock',
                    response.results,
                    '{% trans "Stock Items" %}',
                    renderStockItem,
                    {
                        url: '/stock/item',
                    }
                );
            }
        }
    ));
}


function clearSearchResults() {

    var panel = $('#offcanvas-search');
    
    // Ensure the 'no results found' element is visible
    panel.find('#search-no-results').show();
    
    // Delete any existing search results
    panel.find('#search-results').empty();
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
    
    panel.find('#search-results').append(`
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
