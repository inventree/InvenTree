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

                if (sessionStorage.getItem(key)) {
                    var saved_exp = sessionStorage.getItem(key).split(",");

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
                    sessionStorage.setItem(key, exp);
                });
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            //TODO
        }
    });
}

function openSideNav() {
    document.getElementById("sidenav").style.display = "block";
    document.getElementById("sidenav").style.width = "250px";
    document.getElementById("inventree-content").style.marginLeft = "270px";

    sessionStorage.setItem('inventree-sidenav-state', 'open');


}

function closeSideNav() {
    document.getElementById("sidenav").style.display = "none";
    document.getElementById("sidenav").style.width = "0";
    document.getElementById("inventree-content").style.marginLeft = "0px";

    sessionStorage.setItem('inventree-sidenav-state', 'closed');
}

function toggleSideNav(nav) {
    if ($(nav).width() == 0) {
        openSideNav();
    }
    else {
        closeSideNav();
    }
}

function initSideNav() {
    if (sessionStorage.getItem("inventree-sidenav-state") && sessionStorage.getItem('inventree-sidenav-state') == 'open') {
        openSideNav();
    }
    else {
        closeSideNav();
    }
}