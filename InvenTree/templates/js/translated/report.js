{% load i18n %}

/* globals
    attachSelect,
    closeModal,
    inventreeGet,
    openModal,
    makeOptionsList,
    modalEnable,
    modalSetContent,
    modalSetTitle,
    modalSubmit,
    showAlertDialog,
*/

/* exported
    printReports,
*/

/**
 * Present the user with the available reports,
 * and allow them to select which report to print.
 *
 * The intent is that the available report templates have been requested
 * (via AJAX) from the server.
 */
function selectReport(reports, items, options={}) {

    // If there is only a single report available, just print!
    if (reports.length == 1) {
        if (options.success) {
            options.success(reports[0].pk);
        }

        return;
    }

    var modal = options.modal || '#modal-form';

    var report_list = makeOptionsList(
        reports,
        function(item) {
            var text = item.name;

            if (item.description) {
                text += ` - ${item.description}`;
            }

            return text;
        },
        function(item) {
            return item.pk;
        }
    );

    // Construct form
    var html = '';

    if (items.length > 0) {

        html += `
        <div class='alert alert-block alert-info'>
        ${items.length} {% jstrans "items selected" %}
        </div>`;
    }

    html += `
    <form method='post' action='' class='js-modal-form' enctype='multipart/form-data'>
        <div class='form-group'>
            <label class='control-label requiredField' for='id_report'>
            {% jstrans "Select Report Template" %}
            </label>
            <div class='controls'>
                <select id='id_report' class='select form-control name='report'>
                    ${report_list}
                </select>
            </div>
        </div>
    </form>`;

    openModal({
        modal: modal,
    });

    modalEnable(modal, true);
    modalSetTitle(modal, '{% jstrans "Select Test Report Template" %}');
    modalSetContent(modal, html);

    attachSelect(modal);

    modalSubmit(modal, function() {

        var label = $(modal).find('#id_report');

        var pk = label.val();

        closeModal(modal);

        if (options.success) {
            options.success(pk);
        }
    });

}


/*
 * Print report(s) for the selected items:
 *
 * - Retrieve a list of matching report templates from the server
 * - Present the available templates to the user (if more than one available)
 * - Request printed document
 *
 * Required options:
 * - url: The list URL for the particular template type
 * - items: The list of objects to print
 * - key: The key to use in the query parameters
 */
function printReports(options) {

    if (!options.items || options.items.length == 0) {
        showAlertDialog(
            '{% jstrans "Select Items" %}',
            '{% jstrans "No items selected for printing" }',
        );
        return;
    }

    let params = {
        enabled: true,
    };

    params[options.key] = options.items;

    // Request a list of available report templates
    inventreeGet(options.url, params, {
        success: function(response) {
            if (response.length == 0) {
                showAlertDialog(
                    '{% jstrans "No Reports Found" %}',
                    '{% jstrans "No report templates found which match the selected items" %}',
                );
                return;
            }

            // Select report template for printing
            selectReport(response, options.items, {
                success: function(pk) {
                    let href = `${options.url}${pk}/print/?`;

                    options.items.forEach(function(item) {
                        href += `${options.key}=${item}&`;
                    });

                    window.open(href);
                }
            });
        }
    });
}
