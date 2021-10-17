/* globals
*/

/* exported
    attachNavCallbacks,
    enableNavBar,
    initNavTree,
    loadTree,
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

function loadTree(url, tree, options={}) {
    /* Load the side-nav tree view

    Args:
        url: URL to request tree data
        tree: html ref to treeview
        options:
            data: data object to pass to the AJAX request
            selected: ID of currently selected item
            name: name of the tree
    */

    var data = {};

    if (options.data) {
        data = options.data;
    }

    var key = 'inventree-sidenav-items-';

    if (options.name) {
        key += options.name;
    }

    $.ajax({
        url: url,
        type: 'get',
        dataType: 'json',
        data: data,
        success: function(response) {
            if (response.tree) {
                $(tree).treeview({
                    data: response.tree,
                    enableLinks: true,
                    showTags: true,
                });

                if (localStorage.getItem(key)) {
                    var saved_exp = localStorage.getItem(key).split(',');

                    // Automatically expand the desired notes
                    for (var q = 0; q < saved_exp.length; q++) {
                        $(tree).treeview('expandNode', parseInt(saved_exp[q]));
                    }
                }

                // Setup a callback whenever a node is toggled
                $(tree).on('nodeExpanded nodeCollapsed', function(event, data) {
                    
                    // Record the entire list of expanded items
                    var expanded = $(tree).treeview('getExpanded');

                    var exp = [];

                    for (var i = 0; i < expanded.length; i++) {
                        exp.push(expanded[i].nodeId);
                    }

                    // Save the expanded nodes
                    localStorage.setItem(key, exp);
                });
            }
        },
        error: function(xhr, ajaxOptions, thrownError) {
            // TODO
        }
    });
}


/**
 * Initialize navigation tree display
 */
function initNavTree(options) {

    var resize = true;

    if ('resize' in options) {
        resize = options.resize;
    }

    var label = options.label || 'nav';

    var stateLabel = `${label}-tree-state`;
    var widthLabel = `${label}-tree-width`;

    var treeId = options.treeId || '#sidenav-left';
    var toggleId = options.toggleId;

    // Initially hide the tree
    $(treeId).animate({
        width: '0px',
    }, 0, function() {

        if (resize) {
            $(treeId).resizable({
                minWidth: '0px',
                maxWidth: '500px',
                handles: 'e, se',
                grid: [5, 5],
                stop: function(event, ui) {
                    var width = Math.round(ui.element.width());

                    if (width < 75) {
                        $(treeId).animate({
                            width: '0px'
                        }, 50);

                        localStorage.setItem(stateLabel, 'closed');
                    } else {
                        localStorage.setItem(stateLabel, 'open');
                        localStorage.setItem(widthLabel, `${width}px`);
                    }
                }
            });
        }

        var state = localStorage.getItem(stateLabel);
        var width = localStorage.getItem(widthLabel) || '300px';

        if (state && state == 'open') {

            $(treeId).animate({
                width: width,
            }, 50);
        }
    });

    // Register callback for 'toggle' button
    if (toggleId) {
        
        $(toggleId).click(function() {

            var state = localStorage.getItem(stateLabel) || 'closed';
            var width = localStorage.getItem(widthLabel) || '300px';

            if (state == 'open') {
                $(treeId).animate({
                    width: '0px'
                }, 50);

                localStorage.setItem(stateLabel, 'closed');
            } else {
                $(treeId).animate({
                    width: width,
                }, 50);

                localStorage.setItem(stateLabel, 'open');
            }
        });
    }
}


/**
 * Handle left-hand icon menubar display
 */
function enableNavbar(options) {

    var resize = true;

    if ('resize' in options) {
        resize = options.resize;
    }

    var label = options.label || 'nav';

    label = `navbar-${label}`;

    var stateLabel = `${label}-state`;
    var widthLabel = `${label}-width`;

    var navId = options.navId || '#sidenav-right';

    var toggleId = options.toggleId;

    // Extract the saved width for this element
    $(navId).animate({
        'width': '45px',
        'min-width': '45px',
        'display': 'block',
    }, 50, function() {

        // Make the navbar resizable
        if (resize) {
            $(navId).resizable({
                minWidth: options.minWidth || '100px',
                maxWidth: options.maxWidth || '500px',
                handles: 'e, se',
                grid: [5, 5],
                stop: function(event, ui) {
                    // Record the new width
                    var width = Math.round(ui.element.width());

                    // Reasonably narrow? Just close it!
                    if (width <= 75) {
                        $(navId).animate({
                            width: '45px'
                        }, 50);

                        localStorage.setItem(stateLabel, 'closed');
                    } else {
                        localStorage.setItem(widthLabel, `${width}px`);
                        localStorage.setItem(stateLabel, 'open');
                    }
                }
            });
        }

        var state = localStorage.getItem(stateLabel);

        var width = localStorage.getItem(widthLabel) || '250px';
        
        if (state && state == 'open') {

            $(navId).animate({
                width: width
            }, 100);
        }

    });

    // Register callback for 'toggle' button
    if (toggleId) {

        $(toggleId).click(function() {

            var state = localStorage.getItem(stateLabel) || 'closed';
            var width = localStorage.getItem(widthLabel) || '250px';

            if (state == 'open') {
                $(navId).animate({
                    width: '45px',
                    minWidth: '45px',
                }, 50);

                localStorage.setItem(stateLabel, 'closed');

            } else {

                $(navId).animate({
                    'width': width
                }, 50);

                localStorage.setItem(stateLabel, 'open');
            }
        });
    }
}
