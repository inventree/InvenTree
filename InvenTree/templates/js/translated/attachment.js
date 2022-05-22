{% load i18n %}

/* globals
    makeIconButton,
    renderLink,
*/

/* exported
    addAttachmentButtonCallbacks,
    loadAttachmentTable,
    reloadAttachmentTable,
*/


/*
 * Add callbacks to buttons for creating new attachments.
 *
 * Note: Attachments can also be external links!
 */
function addAttachmentButtonCallbacks(url, fields={}) {

    // Callback for 'new attachment' button
    $('#new-attachment').click(function() {

        var file_fields = {
            attachment: {},
            comment: {},
        };

        Object.assign(file_fields, fields);

        constructForm(url, {
            fields: file_fields,
            method: 'POST',
            onSuccess: reloadAttachmentTable,
            title: '{% trans "Add Attachment" %}',
        });
    });

    // Callback for 'new link' button
    $('#new-attachment-link').click(function() {

        var link_fields = {
            link: {},
            comment: {},
        };

        Object.assign(link_fields, fields);

        constructForm(url, {
            fields: link_fields,
            method: 'POST',
            onSuccess: reloadAttachmentTable,
            title: '{% trans "Add Link" %}',
        });
    });
}


function reloadAttachmentTable() {

    $('#attachment-table').bootstrapTable('refresh');
}


function loadAttachmentTable(url, options) {

    var table = options.table || '#attachment-table';

    setupFilterList('attachments', $(table), '#filter-list-attachments');

    addAttachmentButtonCallbacks(url, options.fields || {});

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

                constructForm(`${url}${pk}/`, {
                    fields: {
                        link: {},
                        comment: {},
                    },
                    processResults: function(data, fields, opts) {
                        // Remove the "link" field if the attachment is a file!
                        if (data.attachment) {
                            delete opts.fields.link;
                        }
                    },
                    onSuccess: reloadAttachmentTable,
                    title: '{% trans "Edit Attachment" %}',
                });
            });

            // Add callback for 'delete' button
            $(table).find('.button-attachment-delete').click(function() {
                var pk = $(this).attr('pk');

                constructForm(`${url}${pk}/`, {
                    method: 'DELETE',
                    confirmMessage: '{% trans "Confirm Delete" %}',
                    title: '{% trans "Delete Attachment" %}',
                    onSuccess: reloadAttachmentTable,
                });
            });
        },
        columns: [
            {
                field: 'attachment',
                title: '{% trans "Attachment" %}',
                formatter: function(value, row) {

                    if (row.attachment) {
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
                    } else if (row.link) {
                        var html = `<span class='fas fa-link'></span> ${row.link}`;
                        return renderLink(html, row.link);
                    } else {
                        return '-';
                    }
                }
            },
            {
                field: 'comment',
                title: '{% trans "Comment" %}',
            },
            {
                field: 'upload_date',
                title: '{% trans "Upload Date" %}',
                formatter: function(value) {
                    return renderDate(value);
                }
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
