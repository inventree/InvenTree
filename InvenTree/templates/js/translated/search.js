{% load i18n %}

/* globals
*/

/* exported
    closeSearchPanel,
    openSearchPanel,
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

}

