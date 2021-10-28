/* globals
*/

/* exported
    enableSidebar,
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
function attachNavCallbacksX(options={}) {

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

/*
 * Activate (display) the selected panel
 */
function activatePanel(label, panel_name, options={}) {

    // First, cause any other panels to "fade out"
    $('.panel-visible').hide();
    $('.panel-visible').removeClass('panel-visible');

    // Find the target panel
    var panel = `#panel-${panel_name}`;
    var select = `#select-${panel_name}`;

    // Check that the selected panel (and select) exist
    if ($(panel).length && $(select).length) {
        // Yep, both are displayed
    } else {
        // Either the select or the panel are not displayed!
        // Iterate through the available 'select' elements until one matches
        panel_name = null;

        $('.sidebar-selector').each(function() {
            var name = $(this).attr('id').replace('select-', '');

            if ($(`#panel-${name}`).length && (panel_name == null)) {
                panel_name = name;
            }

            panel = `#panel-${panel_name}`;
            select = `#select-${panel_name}`;
        });
    }

    // Save the selected panel
    localStorage.setItem(`inventree-selected-panel-${label}`, panel_name);

    // Display the panel
    $(panel).addClass('panel-visible');

    // Load the data
    $(panel).trigger('fadeInStarted');

    $(panel).fadeIn(100, function() {
    });

    // Un-select all selectors
    $('.list-group-item').removeClass('active');

    // Find the associated selector
    var selector = `#select-${panel_name}`;

    $(selector).addClass('active');
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
 * Enable support for sidebar on this page
 */
function enableSidebar(label, options) {

    // Enable callbacks for sidebar buttons
    $('.sidebar-selector').click(function() {
        var el = $(this);

        // Find the matching panel element to display
        var panel_name = el.attr('id').replace('select-', '');

        activatePanel(label, panel_name, options);
    });

    /* Look for a "default" panel to initialize for this page
     *
     * - First preference = URL parameter e.g. ?display=part-stock
     * - Second preference = local storage
     * - Third preference = default
     */

    var selected_panel = $.urlParam('display') || localStorage.getItem(`inventree-selected-panel-${label}`) || options.default;

    if (selected_panel) {
        activatePanel(label, selected_panel);
    } else {
        // Find the "first" available panel (according to the sidebar)
        var selector = $('.sidebar-selector').first();
        
        var panel_name = selector.attr('id').replace('select-', '');
        
        activatePanel(label, panel_name);
    }

    // Add callback to "collapse" and "expand" the sidebar
    $('#sidebar-toggle').click(function() {

        // By default, the menu is "expanded"
        var state = localStorage.getItem(`inventree-menu-state-${label}`) || 'expanded';
        
        // We wish to "toggle" the state!
        setSidebarState(label, state == "expanded" ? "collapsed" : "expanded");
    });
    
    // Set the initial state (default = expanded)
    var state = localStorage.getItem(`inventree-menu-state-${label}`) || 'expanded';

    setSidebarState(label, state);

    // Finally, show the sidebar
    $('#sidebar').show();
}


/*
 * Set the "toggle" state of the sidebar
 */
function setSidebarState(label, state) {

    if (state == "collapsed") {
        $('.sidebar-item-text').animate({
            opacity: 0.0,
        }, 100, function() {
            $('.sidebar-item-text').hide();
            $('#sidebar-toggle-icon').removeClass('fa-chevron-left').addClass('fa-chevron-right');
        });
    } else {
        $('.sidebar-item-text').show();
        $('#sidebar-toggle-icon').removeClass('fa-chevron-right').addClass('fa-chevron-left');
        $('.sidebar-item-text').animate({
            opacity: 1.0,
        }, 100);
    }

    // Save the state of this sidebar
    localStorage.setItem(`inventree-menu-state-${label}`, state);
}


/**
 * Handle left-hand icon menubar display
 */
function enableNavbarX(options) {

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
