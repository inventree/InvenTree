/* globals
*/

/* exported
    attachNavCallbacks,
    onPanelLoad,
*/

/*
* Attach callbacks to navigation bar elements.
*
* Searches for elements with the class 'nav-toggle'.
* A callback is added to each element,
* to display the matching panel.
*
* The 'id' of the .nav-toggle element should be of the form "select-<x>",
* and point to a matching "panel-<x>"
*/
function attachNavCallbacks(options={}) {

    $('.nav-toggle').click(function() {
        var el = $(this);

        // Find the matching "panel" element
        var panelName = el.attr('id').replace('select-', '');

        activatePanel(panelName, options);
    });

    var panelClass = options.name || 'unknown';

    /* Look for a default panel to initialize
     * First preference = URL parameter e.g. ?display=part-stock
     * Second preference = localStorage
     * Third preference = default
     */
    var defaultPanel = $.urlParam('display') || localStorage.getItem(`inventree-selected-panel-${panelClass}`) || options.default;

    if (defaultPanel) {
        activatePanel(defaultPanel);
    }
}


function activatePanel(panelName, options={}) {

    var panelClass = options.name || 'unknown';

    // First, cause any other panels to "fade out"
    $('.panel-visible').hide();
    $('.panel-visible').removeClass('panel-visible');
    
    // Find the target panel
    var panel = `#panel-${panelName}`;
    var select = `#select-${panelName}`;

    // Check that the selected panel (and select) exist
    if ($(panel).length && $(select).length) {
        // Yep, both are displayed
    } else {
        // Either the select or the panel are not displayed!
        // Iterate through the available 'select' elements until one matches
        panelName = null;

        $('.nav-toggle').each(function() {
            var panel_name = $(this).attr('id').replace('select-', '');

            if ($(`#panel-${panel_name}`).length && (panelName == null)) {
                panelName = panel_name;
            }

            panel = `#panel-${panelName}`;
            select = `#select-${panelName}`;
        });
    }

    // Save the selected panel
    localStorage.setItem(`inventree-selected-panel-${panelClass}`, panelName);

    // Display the panel
    $(panel).addClass('panel-visible');

    // Load the data
    $(panel).trigger('fadeInStarted');

    $(panel).fadeIn(100, function() {
    });

    // Un-select all selectors
    $('.list-group-item').removeClass('active');

    // Find the associated selector
    var selectElement = `#select-${panelName}`;

    $(selectElement).parent('.list-group-item').addClass('active');
}


function onPanelLoad(panel, callback) {
    // One-time callback when a panel is first displayed
    // Used to implement lazy-loading, rather than firing 
    // multiple AJAX queries when the page is first loaded.

    var panelId = `#panel-${panel}`;

    $(panelId).on('fadeInStarted', function() {

        // Trigger the callback
        callback();

        // Turn off the event
        $(panelId).off('fadeInStarted');

    });
}
