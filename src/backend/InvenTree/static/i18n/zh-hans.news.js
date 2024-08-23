



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
            ordering: '-published',
            read: false,
        },
        paginationVAlign: 'bottom',
        formatNoMatches: function() {
            return '未找到新闻';
        },
        columns: [
            {
                field: 'pk',
                title: 'ID',
                visible: false,
                switchable: false,
            },
            {
                field: 'title',
                title: '标题',
                sortable: 'true',
                formatter: function(value, row) {
                    return `<a href="` + row.link + `">` + value + `</a>`;
                }
            },
            {
                field: 'summary',
                title: '摘要',
            },
            {
                field: 'author',
                title: '作者',
            },
            {
                field: 'published',
                title: '已发布',
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
