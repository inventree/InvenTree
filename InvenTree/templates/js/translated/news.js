{% load i18n %}
{% load inventree_extras %}

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
        },
        paginationVAlign: 'bottom',
        formatNoMatches: function() {
            return '{% trans "No news found" %}';
        },
        columns: [
            {
                field: 'pk',
                title: '{% trans "ID" %}',
                visible: false,
                switchable: false,
            },
            {
                field: 'title',
                title: '{% trans "Title" %}',
                sortable: 'true',
                formatter: function(value, row) {
                    return `<a href="` + row.link + `">` + value + `</a>`;
                }
            },
            {
                field: 'summary',
                title: '{% trans "Summary" %}',
            },
            {
                field: 'author',
                title: '{% trans "Author" %}',
            },
            {
                field: 'published',
                title: '{% trans "Published" %}',
                sortable: 'true',
                formatter: function(value) {
                    return renderDate(value);
                }
            },
        ]
    });
}
