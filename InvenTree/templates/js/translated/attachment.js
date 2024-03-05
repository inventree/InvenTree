{% load i18n %}

/* globals
    constructForm,
    getTableData,
    enableDragAndDrop,
    makeDeleteButton,
    makeEditButton,
    makeIcon,
    reloadBootstrapTable,
    renderDate,
    renderLink,
    setupFilterList,
    showApiError,
    wrapButtons,
*/

/* exported
    attachmentLink,
    addAttachmentButtonCallbacks,
    loadAttachmentTable
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
            comment: {
                icon: 'fa-comment',
            },
        };

        Object.assign(file_fields, fields);

        constructForm(url, {
            fields: file_fields,
            method: 'POST',
            refreshTable: '#attachment-table',
            title: '{% trans "Add Attachment" %}',
        });
    });

    // Callback for 'new link' button
    $('#new-attachment-link').click(function() {

        var link_fields = {
            link: {
                icon: 'fa-link',
            },
            comment: {
                icon: 'fa-comment',
            },
        };

        Object.assign(link_fields, fields);

        constructForm(url, {
            fields: link_fields,
            method: 'POST',
            refreshTable: '#attachment-table',
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
            icon = makeIcon(attachmentIcon(attachment.filename), '');
        } else if (attachment.link) {
            icon = makeIcon('fa-link', '');
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
        multi_delete: true,
        title: '{% trans "Delete Attachments" %}',
        preFormContent: html,
        form_data: {
            items: ids,
            filters: options.filters,
        },
        refreshTable: '#attachment-table',
    });
}


/*
 * Return a particular icon based on filename extension
 */
function attachmentIcon(filename) {
    // Default file icon (if no better choice is found)
    let icon = 'fa-file-alt';
    let fn = filename.toLowerCase();

    // Look for some "known" file types
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
        let images = ['.png', '.jpg', '.bmp', '.gif', '.svg', '.tif'];

        images.forEach(function(suffix) {
            if (fn.endsWith(suffix)) {
                icon = 'fa-file-image';
            }
        });
    }

    return icon;
}


/*
 * Render a link (with icon) to an internal attachment (file)
 */
function attachmentLink(filename) {

    if (!filename) {
        return null;
    }

    let split = filename.split('/');
    let fn = split[split.length - 1];

    let icon = attachmentIcon(filename);

    let html = makeIcon(icon) + ` ${fn}`;

    return renderLink(html, filename, {download: true});
}


/*
 * Construct a set of actions for an attachment table,
 * with the provided permission set
 */
function makeAttachmentActions(permissions, options) {

    let actions = [];

    if (permissions.delete) {
        actions.push({
            label: 'delete',
            icon: 'fa-trash-alt icon-red',
            title: '{% trans "Delete attachments" %}',
            callback: options.callback,
        });
    }

    return actions;
}


/* Load a table of attachments against a specific model.
 * Note that this is a 'generic' table which is used for multiple attachment model classes
 */
function loadAttachmentTable(url, options) {

    var table = options.table || '#attachment-table';

    var permissions = {};

    // First we determine which permissions the user has for this attachment table
    $.ajax({
        url: url,
        async: false,
        type: 'OPTIONS',
        contentType: 'application/json',
        dataType: 'json',
        accepts: {
            json: 'application/json',
        },
        success: function(response) {
            if (response.actions.DELETE) {
                permissions.delete = true;
            }

            if (response.actions.POST) {
                permissions.change = true;
                permissions.add = true;
            }
        },
        error: function(xhr) {
            showApiError(xhr, url);
        }
    });

    setupFilterList('attachments', $(table), '#filter-list-attachments', {
        custom_actions: [
            {
                label: 'attachments',
                icon: 'fa-tools',
                title: '{% trans "Attachment actions" %}',
                actions: makeAttachmentActions(permissions, {
                    callback: function(attachments) {
                        deleteAttachments(attachments, url, options);
                    }
                }),
            }
        ]
    });

    if (permissions.add) {
        addAttachmentButtonCallbacks(url, options.fields || {});
    } else {
        // Hide the buttons
        $('#new-attachment').hide();
        $('#new-attachment-link').hide();
    }

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
        sidePagination: 'server',
        onPostBody: function() {

            // Add callback for 'delete' button
            if (permissions.delete) {
                $(table).find('.button-attachment-delete').click(function() {
                    let pk = $(this).attr('pk');
                    let attachments = $(table).bootstrapTable('getRowByUniqueId', pk);

                    deleteAttachments([attachments], url, options);
                });
            }

            // Add callback for 'edit' button
            if (permissions.change) {
                $(table).find('.button-attachment-edit').click(function() {
                    let pk = $(this).attr('pk');

                    constructForm(`${url}${pk}/`, {
                        fields: {
                            link: {
                                icon: 'fa-link',
                            },
                            comment: {
                                icon: 'fa-comment',
                            },
                        },
                        processResults: function(data, fields, opts) {
                            // Remove the "link" field if the attachment is a file!
                            if (data.attachment) {
                                delete opts.fields.link;
                            }
                        },
                        refreshTable: '#attachment-table',
                        title: '{% trans "Edit Attachment" %}',
                    });
                });
            }
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
                        return attachmentLink(row.attachment);
                    } else if (row.link) {
                        let html = makeIcon('fa-link') + ` ${row.link}`;
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
                sortable: true,
                title: '{% trans "Upload Date" %}',
                formatter: function(value, row) {
                    var html = renderDate(value);

                    if (row.user_detail) {
                        html += `<span class='badge bg-dark rounded-pill float-right'>${row.user_detail.username}</span>`;
                    }

                    return html;
                }
            },
            {
                field: 'actions',
                formatter: function(value, row) {
                    let buttons = '';

                    if (permissions.change) {
                        buttons += makeEditButton(
                            'button-attachment-edit',
                            row.pk,
                            '{% trans "Edit attachment" %}',
                        );
                    }

                    if (permissions.delete) {
                        buttons += makeDeleteButton(
                            'button-attachment-delete',
                            row.pk,
                            '{% trans "Delete attachment" %}',
                        );
                    }

                    return wrapButtons(buttons);
                }
            }
        ]
    });

    // Enable drag-and-drop functionality
    enableDragAndDrop(
        '#attachment-dropzone',
        url,
        {
            data: options.filters,
            label: 'attachment',
            method: 'POST',
            success: function() {
                reloadBootstrapTable('#attachment-table');
            }
        }
    );
}
