{% load i18n %}
{% load inventree_extras %}


/* globals
    getReadEditButton,
    inventreePut,
    renderDate,
    setupFilterList,
*/


/* exported
    loadNewsFeedTable,
*/

/*
 * Load notification table
 */
function loadNewsFeedTable(table, options={}, enableDelete=false) {
    setupFilterList('news', table);

    $(table).inventreeTable({
        url: options.url,
        name: 'news',
        groupBy: false,
        queryParams: {
            ordering: 'published',
            read: false,
        },
        paginationVAlign: 'bottom',
        formatNoMatches: function() {
            return '{% jstrans "No news found" %}';
        },
        columns: [
            {
                field: 'pk',
                title: '{% jstrans "ID" %}',
                visible: false,
                switchable: false,
            },
            {
                field: 'title',
                title: '{% jstrans "Title" %}',
                sortable: 'true',
                formatter: function(value, row) {
                    return `<a href="` + row.link + `">` + value + `</a>`;
                }
            },
            {
                field: 'summary',
                title: '{% jstrans "Summary" %}',
            },
            {
                field: 'author',
                title: '{% jstrans "Author" %}',
            },
            {
                field: 'published',
                title: '{% jstrans "Published" %}',
                sortable: 'true',
                formatter: function(value, row) {
                    var html = renderDate(value);
                    var buttons = getReadEditButton(row.pk, row.read);
                    html += `<div class='btn-group float-right' role='group'>${buttons}</div>`;
                    return html;
                }
            },
        ]
    });

    $(table).on('click', '.notification-read', function() {
        var pk = $(this).attr('pk');

        var url = `/api/news/${pk}/`;

        inventreePut(url,
            {
                read: true,
            },
            {
                method: 'PATCH',
                success: function() {
                    $(table).bootstrapTable('refresh');
                }
            }
        );
    });
}
