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

    // Ensure the 'no results found' element is visible
    panel.find('#search-no-results').show();

    // Finally, grab keyboard focus in the search bar
    panel.find('#search-input').focus();

    panel.find('#search-input').on('keyup change', searchTextChanged);

}

var searchRequests = [];
var searchInputTimer = null;
var searchText = null;
var searchTextPrevious = null;

function searchTextChanged(event) {

    searchText = $('#offcanvas-search').find('#search-input').val();

    clearTimeout(searchInputTimer);
    searchInputTimer = setTimeout(updateSearch, 250);
};


function updateSearch() {

    if (searchText == searchTextPrevious) {
        return;
    }

    if (searchText.length == 0) {
        return;
    }

    searchTextPrevious = searchText;

    // Search for matching parts
    inventreeGet(
        `{% url "api-part-list" %}`,
        {
            search: searchText,
            limit: 10,
            offset: 0,
        },
        {
            success: function(results) {
                // TODO
            }
        }
    );

    // Search for matching stock items
    inventreeGet(
        '{% url "api-stock-list" %}',
        {
            search: searchText,
            limit: 10,
            offset: 0,
        },
        {
            success: function(results) {
                // TODO
            }
        }
    )

}