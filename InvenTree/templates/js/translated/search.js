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
                addSearchResults('part', response.results, '{% trans "Parts" %}');
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
        },
        {
            success: function(response) {
                addSearchResults('stock', response.results, '{% trans "Stock Items" %}');
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
function addSearchResults(key, results, title, formatter) {
    
    if (results.length == 0) {
        // Do not display this group, as there are no results
        return;
    }

    var panel = $('#offcanvas-search');

    // Ensure the 'no results found' element is hidden
    panel.find('#search-no-results').hide();

    var results_element = panel.find('#search-results');
    
    var header = `search-results-${key}`;
    
    panel.find('#search-results').append(`
        <div class='search-result-group' id='${header}'>
            <h5>${title}</h5>
        </div>
    `);

    results.forEach(function(result) {
        // results_html.append(formatter(result));
        var result_html = `<div class='search-result-entry'>hello result</div>`;

        panel.find(`#${header}`).append(result_html);
    });
}