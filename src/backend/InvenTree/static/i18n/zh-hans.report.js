

/* globals
    attachSelect,
    closeModal,
    constructForm,
    inventreeGet,
    openModal,
    makeOptionsList,
    modalEnable,
    modalSetContent,
    modalSetTitle,
    modalSubmit,
    showAlertDialog,
    showMessage,
*/

/* exported
    printReports,
*/


/*
 * Print report(s) for the selected items:
 *
 * - Retrieve a list of matching report templates from the server
 * - Present the available templates to the user (if more than one available)
 * - Request printed document
 *
 * Required options:
 * - model_type: The "type" of report template to print against
 * - items: The list of objects to print
 */
function printReports(model_type, items) {

    if (!items || items.length == 0) {
        showAlertDialog(
            '选择项目',
            '未选择要打印的项目',
        );
        return;
    }

    // Join the items with a comma character
    const item_string = items.join(',');

    constructForm('/api/report/print/', {
        method: 'POST',
        title: '打印报告',
        fields: {
            template: {
                filters: {
                    enabled: true,
                    model_type: model_type,
                    items: item_string,
                }
            },
            items: {
                hidden: true,
                value: items,
            }
        },
        onSuccess: function(response) {
            if (response.complete) {
                if (response.output) {
                    window.open(response.output, '_blank');
                } else {
                    showMessage('报告打印成功', {
                        style: 'success'
                    });
                }
            } else {
                showMessage('报告打印失败', {
                    style: 'warning',
                });
            }
        }
    })
}
