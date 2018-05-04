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