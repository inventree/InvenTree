
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

        console.log("no match for panel:", panelName);

        $('.nav-toggle').each(function(item) {
            var panel_name = $(this).attr('id').replace('select-', '');

            console.log("checking:", panel_name);

            if ($(`#panel-${panel_name}`).length && (panelName == null)) {
                console.log("found match -", panel_name);
                panelName = panel_name;
            }
        });
    }

    // Save the selected panel
    localStorage.setItem(`inventree-selected-panel-${panelClass}`, panelName);

    // Display the panel
    $(panel).addClass('panel-visible');
    $(panel).fadeIn(100);

    // Un-select all selectors
    $('.list-group-item').removeClass('active');

    // Find the associated selector
    var select = `#select-${panelName}`;

    $(select).parent('.list-group-item').addClass('active');
}