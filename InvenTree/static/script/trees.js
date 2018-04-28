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