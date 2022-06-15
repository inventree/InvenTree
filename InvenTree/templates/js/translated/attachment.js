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


/*
 * Construct a form to delete attachment files
 */
function deleteAttachments(attachments, url, options={}) {

    if (attachments.length == 0) {
        console.warn('deleteAttachments function called with zero attachments provided');
        return;
    }

    function renderAttachment(attachment, opts={}) {

        var icon = '';

        if (attachment.filename) {
            icon = `<span class='fas fa-file-alt'></span>`;
        } else if (attachment.link) {
            icon = `<span class='fas fa-link'></span>`;
        }

        return `
        <tr>
            <td>${icon}</td>
            <td>${attachment.filename || attachment.link}</td>
            <td>${attachment.comment}</td>
        </tr>`;
    }

    var rows = '';
    var ids = [];

    attachments.forEach(function(att) {
        rows += renderAttachment(att);
        ids.push(att.pk);
    });

    var html = `
    <div class='alert alert-block alert-danger'>
    {% trans "All selected attachments will be deleted" %}
    </div>
    <table class='table table-striped table-condensed'>
    <tr>
        <th></th>
        <th>{% trans "Attachment" %}</th>
        <th>{% trans "Comment" %}</th>
    </tr>
    ${rows}
    </table>
    `;

    constructForm(url, {
        method: 'DELETE',
        title: '{% trans "Delete Attachments" %}',
        preFormContent: html,
        form_data: {
            items: ids,
            filters: options.filters,
        },
        onSuccess: function() {
            // Refresh the table once all attachments are deleted
            $('#attachment-table').bootstrapTable('refresh');
        }
    });
}


function reloadAttachmentTable() {

    $('#attachment-table').bootstrapTable('refresh');
}


/* Load a table of attachments against a specific model.
 * Note that this is a 'generic' table which is used for multiple attachment model classes
 */
function loadAttachmentTable(url, options) {

    var table = options.table || '#attachment-table';

    setupFilterList('attachments', $(table), '#filter-list-attachments');

    addAttachmentButtonCallbacks(url, options.fields || {});

    // Add callback for the 'multi delete' button
    $('#multi-attachment-delete').click(function() {
        var attachments = getTableData(table);

        if (attachments.length > 0) {
            deleteAttachments(attachments, url, options);
        }
    });

    $(table).inventreeTable({
        url: url,
        name: options.name || 'attachments',
        formatNoMatches: function() {
            return '{% trans "No attachments found" %}';
        },
        sortable: true,
        search: true,
        queryParams: options.filters || {},
        uniqueId: 'pk',
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

                var attachment = $(table).bootstrapTable('getRowByUniqueId', pk);
                deleteAttachments([attachment], url, options);
            });
        },
        columns: [
            {
                checkbox: true,
            },
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

                        return renderLink(html, value, {download: true});
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
                formatter: function(value, row) {
                    var html = renderDate(value);

                    if (row.user_detail) {
                        html += `<span class='badge bg-dark rounded-pill float-right'>${row.user_detail.username}</div>`;
                    }

                    return html;
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
