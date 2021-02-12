{% load i18n %}


function selectReport(reports, items, options={}) {
    /**
     * Present the user with the available reports,
     * and allow them to select which report to print.
     * 
     * The intent is that the available report templates have been requested
     * (via AJAX) from the server.
     */

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
        ${items.length} {% trans "items selected" %}
        </div>`;
    }

    html += `
    <form method='post' action='' class='js-modal-form' enctype='multipart/form-data'>
        <div class='form-group'>
            <label class='control-label requiredField' for='id_report'>
            {% trans "Select Report Template" %}
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
    modalSetTitle(modal, '{% trans "Select Test Report Template" %}');
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


function printTestReports(items, options={}) {
    /**
     * Print test reports for the provided stock item(s)
     */

    if (items.length == 0) {
        showAlertDialog(
            '{% trans "Select Stock Items" %}',
            '{% trans "Stock item(s) must be selected before printing reports" %}'
        );

        return;
    }

    // Request available labels from the server
    inventreeGet(
        '{% url "api-stockitem-testreport-list" %}',
        {
            enabled: true,
            items: items,
        },
        {
            success: function(response) {
                if (response.length == 0) {
                    showAlertDialog(
                        '{% trans "No Reports Found" %}',
                        '{% trans "No report templates found which match selected stock item(s)" %}',
                    );

                    return;
                }

                // Select report template to print
                selectReport(
                    response,
                    items,
                    {
                        success: function(pk) {
                            var href = `/api/report/test/${pk}/print/?`;

                            items.forEach(function(item) {
                                href += `items[]=${item}&`;
                            });

                            window.location.href = href;
                        }
                    }
                );
            }
        }
    );
}