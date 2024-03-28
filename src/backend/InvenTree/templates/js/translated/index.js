{% load i18n %}

/* globals
    addSidebarHeader,
    addSidebarItem,
    checkPermission,
    global_settings,
    imageHoverIcon,
    makeProgressBar,
    renderLink,
    shortenString,
    user_settings,
    withTitle,
*/

/* exported
    addHeaderAction,
    addHeaderTitle,
*/


/*
 * Add a 'header title' to the index sidebar
 */
function addHeaderTitle(title) {
    addSidebarHeader({
        text: title,
    });
}


function addHeaderAction(label, title, icon, options) {

    // Construct a "badge" to add to the sidebar item
    var badge = `
    <span id='sidebar-badge-${label}' class='sidebar-item-badge badge rounded-pill badge-right bg-dark'>
        <span class='fas fa-spin fa-spinner'></span>
    </span>
    `;

    addSidebarItem({
        label: label,
        text: title,
        icon: icon,
        content_after: badge
    });

    // Add a detail item to the detail item-panel
    $("#detail-panels").append(
        `<div class='panel panel-inventree panel-hidden' id='panel-${label}'>
            <div class='panel-heading'>
                <h4>${title}</h4>
            </div>
            <div class='panel-content'>
                <table class='table table-condensed table-striped' id='table-${label}'></table>
            </div>
        </div>`
    );

    let table_name = `#table-${label}`;

    // Connect a callback to the table
    $(table_name).on('load-success.bs.table', function(data) {

        let options = $(table_name).bootstrapTable('getOptions');

        let count = options.totalRows;

        if (count == undefined || count == null) {
            let data = $(table_name).bootstrapTable('getData');
            count = data.length;
        }

        let badge = $(`#sidebar-badge-${label}`);

        badge.html(count);

        if (count > 0) {
            badge.removeClass('bg-dark');
            badge.addClass('bg-primary');
        }
    });
}


/*
 * Load a table displaying parts which are outstanding for builds
 */
function loadRequiredForBuildsPartsTable(table, options={}) {
    let name = 'parts-required-for-builds';

    let params = {
        stock_to_build: true,
    };

    $(table).inventreeTable({
        url: '{% url "api-part-list" %}',
        queryParams: params,
        name: name,
        showColumns: false,
        search: false,
        sortable: false,
        formatNoMatches: function() {
            return '{% trans "No parts required for builds" %}';
        },
        columns: [
            {
                field: 'name',
                title: '{% trans "Part" %}',
                formatter: function(value, row) {
                    let name = shortenString(row.full_name);
                    let display= imageHoverIcon(row.thumbnail) + renderLink(name, `/part/${row.pk}/`);

                    return withTitle(display, row.full_name);
                }
            },
            {
                field: 'description',
                title: '{% trans "Description" %}',
            },
            {
                field: 'total_in_stock',
                title: '{% trans "Available" %}',
                formatter: function(value, row) {
                    return value;
                }
            },
            {
                field: 'allocated_to_build_orders',
                title: '{% trans "Allocated Stock" %}',
                formatter: function(_value, row) {
                    return makeProgressBar(
                        row.allocated_to_build_orders,
                        row.required_for_build_orders,
                    );
                }
            },
        ]
    });
}
