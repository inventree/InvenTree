function loadTree(url, tree, data) {

    $.ajax({
        url: url,
        type: 'get',
        dataType: 'json',
        data: data,
        success: function (response) {
            if (response.tree) {
                $(tree).treeview({
                    data: response.tree,
                    enableLinks: true
                });

                var saved_exp = sessionStorage.getItem('inventree-sidenav-expanded-items').split(",");

                // Automatically expand the desired notes
                for (var q = 0; q < saved_exp.length; q++) {
                    $(tree).treeview('expandNode', parseInt(saved_exp[q]));
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
                    sessionStorage.setItem('inventree-sidenav-expanded-items', exp);
                });
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            //TODO
        }
    });
}

function openSideNav() {
    document.getElementById("sidenav").style.width = "250px";
    document.getElementById("inventree-content").style.marginLeft = "270px";

    sessionStorage.setItem('inventree-sidenav-state', 'open');


}

function closeSideNav() {
    document.getElementById("sidenav").style.width = "0";
    document.getElementById("inventree-content").style.marginLeft = "50px";

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