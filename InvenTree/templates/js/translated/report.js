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
    printBomReports,
    printBuildReports,
    printPurchaseOrderReports,
    printSalesOrderReports,
    printTestReports,
*/

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


function printTestReports(items) {
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

    // Request available reports from the server
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
                                href += `item=${item}&`;
                            });

                            window.location.href = href;
                        }
                    }
                );
            }
        }
    );
}


function printBuildReports(builds) {
    /**
     * Print Build report for the provided build(s)
     */

    if (builds.length == 0) {
        showAlertDialog(
            '{% trans "Select Builds" %}',
            '{% trans "Build(s) must be selected before printing reports" %}',
        );

        return;
    }

    inventreeGet(
        '{% url "api-build-report-list" %}',
        {
            enabled: true,
            builds: builds,
        },
        {
            success: function(response) {
                if (response.length == 0) {
                    showAlertDialog(
                        '{% trans "No Reports Found" %}',
                        '{% trans "No report templates found which match selected build(s)" %}'
                    );

                    return;
                }

                // Select which report to print
                selectReport(
                    response,
                    builds,
                    {
                        success: function(pk) {
                            var href = `/api/report/build/${pk}/print/?`;

                            builds.forEach(function(build) {
                                href += `build=${build}&`;
                            });

                            window.location.href = href;
                        }
                    }
                );
            }
        }
    );
}


function printBomReports(parts) {
    /**
     * Print BOM reports for the provided part(s)
     */

    if (parts.length == 0) {
        showAlertDialog(
            '{% trans "Select Parts" %}',
            '{% trans "Part(s) must be selected before printing reports" %}'
        );

        return;
    }

    // Request available reports from the server
    inventreeGet(
        '{% url "api-bom-report-list" %}',
        {
            enabled: true,
            parts: parts,
        },
        {
            success: function(response) {
                if (response.length == 0) {
                    showAlertDialog(
                        '{% trans "No Reports Found" %}',
                        '{% trans "No report templates found which match selected part(s)" %}',
                    );

                    return;
                }

                // Select which report to print
                selectReport(
                    response,
                    parts,
                    {
                        success: function(pk) {
                            var href = `/api/report/bom/${pk}/print/?`;

                            parts.forEach(function(part) {
                                href += `part=${part}&`;
                            });

                            window.location.href = href;
                        }
                    }
                );
            }
        }
    );
}


function printPurchaseOrderReports(orders) {
    /**
     * Print PurchaseOrder reports for the provided purchase order(s)
     */

    if (orders.length == 0) {
        showAlertDialog(
            '{% trans "Select Purchase Orders" %}',
            '{% trans "Purchase Order(s) must be selected before printing report" %}',
        );

        return;
    }

    // Request avaiable report templates
    inventreeGet(
        '{% url "api-po-report-list" %}',
        {
            enabled: true,
            orders: orders,
        },
        {
            success: function(response) {
                if (response.length == 0) {
                    showAlertDialog(
                        '{% trans "No Reports Found" %}',
                        '{% trans "No report templates found which match selected orders" %}',
                    );

                    return;
                }

                // Select report template
                selectReport(
                    response,
                    orders,
                    {
                        success: function(pk) {
                            var href = `/api/report/po/${pk}/print/?`;

                            orders.forEach(function(order) {
                                href += `order=${order}&`;
                            });

                            window.location.href = href;
                        }
                    }
                );
            }
        }
    );
}


function printSalesOrderReports(orders) {
    /**
     * Print SalesOrder reports for the provided purchase order(s)
     */

    if (orders.length == 0) {
        showAlertDialog(
            '{% trans "Select Sales Orders" %}',
            '{% trans "Sales Order(s) must be selected before printing report" %}',
        );

        return;
    }

    // Request avaiable report templates
    inventreeGet(
        '{% url "api-so-report-list" %}',
        {
            enabled: true,
            orders: orders,
        },
        {
            success: function(response) {
                if (response.length == 0) {
                    showAlertDialog(
                        '{% trans "No Reports Found" %}',
                        '{% trans "No report templates found which match selected orders" %}',
                    );

                    return;
                }

                // Select report template
                selectReport(
                    response,
                    orders,
                    {
                        success: function(pk) {
                            var href = `/api/report/so/${pk}/print/?`;

                            orders.forEach(function(order) {
                                href += `order=${order}&`;
                            });

                            window.location.href = href;
                        }
                    }
                );
            }
        }
    );
}
