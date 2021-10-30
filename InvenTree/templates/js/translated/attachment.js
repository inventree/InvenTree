{% load i18n %}

/* globals
    makeIconButton,
    renderLink,
*/

/* exported
    loadAttachmentTable,
    reloadAttachmentTable,
*/

function reloadAttachmentTable() {

    $('#attachment-table').bootstrapTable('refresh');
}


function loadAttachmentTable(url, options) {

    var table = options.table || '#attachment-table';

    $(table).inventreeTable({
        url: url,
        name: options.name || 'attachments',
        formatNoMatches: function() {
            return '{% trans "No attachments found" %}';
        },
        sortable: true,
        search: true,
        queryParams: options.filters || {},
        onPostBody: function() {
            // Add callback for 'edit' button
            $(table).find('.button-attachment-edit').click(function() {
                var pk = $(this).attr('pk');

                if (options.onEdit) {
                    options.onEdit(pk);
                }
            });
            
            // Add callback for 'delete' button
            $(table).find('.button-attachment-delete').click(function() {
                var pk = $(this).attr('pk');

                if (options.onDelete) {
                    options.onDelete(pk);
                }
            });
        },
        columns: [
            {
                field: 'attachment',
                title: '{% trans "File" %}',
                formatter: function(value) {

                    var icon = 'fa-file-alt';

                    var fn = value.toLowerCase();

                    if (fn.endsWith('.csv')) {
                        icon = 'fa-file-csv';
                    } else if (fn.endsWith('.pdf')) {
                        icon = 'fa-file-pdf';
                    } else if (fn.endsWith('.xls') || fn.endsWith('.xlsx')) {
                        icon = 'fa-file-excel';
                    } else if (fn.endsWith('.doc') || fn.endsWith('.docx')) {
                        icon = 'fa-file-word';
                    } else if (fn.endsWith('.zip') || fn.endsWith('.7z')) {
                        icon = 'fa-file-archive';
                    } else {
                        var images = ['.png', '.jpg', '.bmp', '.gif', '.svg', '.tif'];

                        images.forEach(function(suffix) {
                            if (fn.endsWith(suffix)) {
                                icon = 'fa-file-image';
                            }
                        });
                    }

                    var split = value.split('/');
                    var filename = split[split.length - 1];

                    var html = `<span class='fas ${icon}'></span> ${filename}`;

                    return renderLink(html, value);
                }
            },
            {
                field: 'comment',
                title: '{% trans "Comment" %}',
            },
            {
                field: 'upload_date',
                title: '{% trans "Upload Date" %}',
            },
            {
                field: 'actions',
                formatter: function(value, row) {
                    var html = '';

                    html = `<div class='btn-group float-right' role='group'>`;

                    html += makeIconButton(
                        'fa-edit icon-blue',
                        'button-attachment-edit',
                        row.pk,
                        '{% trans "Edit attachment" %}',
                    );

                    html += makeIconButton(
                        'fa-trash-alt icon-red',
                        'button-attachment-delete',
                        row.pk,
                        '{% trans "Delete attachment" %}',
                    );

                    html += `</div>`;

                    return html;
                }
            }
        ]
    });
}
