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

    var key = "inventree-sidenav-items-";

    if (options.name) {
        key += options.name;
    }

    $.ajax({
        url: url,
        type: 'get',
        dataType: 'json',
        data: data,
        success: function (response) {
            if (response.tree) {
                $(tree).treeview({
                    data: response.tree,
                    enableLinks: true,
                    showTags: true,
                });

                if (localStorage.getItem(key)) {
                    var saved_exp = localStorage.getItem(key).split(",");

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
        error: function (xhr, ajaxOptions, thrownError) {
            //TODO
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
        width: '45px',
        'min-width': '45px',
        display: 'block',
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