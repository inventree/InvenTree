
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

    // Look for a default panel to initialize
    var defaultPanel = localStorage.getItem(`inventree-selected-panel-${panelClass}`) || options.default;

    if (defaultPanel) {
        activatePanel(defaultPanel);
    }
}


function activatePanel(panelName, options={}) {

    var panelClass = options.name || 'unknown';

    // Save the selected panel
    localStorage.setItem(`inventree-selected-panel-${panelClass}`, panelName);

    // First, cause any other panels to "fade out"
    $('.panel-visible').hide();
    $('.panel-visible').removeClass('panel-visible');

    // Find the target panel
    var panel = `#panel-${panelName}`;

    // Display the panel
    $(panel).addClass('panel-visible');
    $(panel).fadeIn(100);

    // Un-select all selectors
    $('.list-group-item').removeClass('active');

    // Find the associated selector
    var select = `#select-${panelName}`;

    $(select).parent('.list-group-item').addClass('active');
}