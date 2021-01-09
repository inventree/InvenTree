{% load i18n %}

function selectLabel(labels, options={}) {
    /**
     * Present the user with the available labels,
     * and allow them to select which label to print.
     * 
     * The intent is that the available labels have been requested
     * (via AJAX) from the server.
     */

    var modal = options.modal || '#modal-form';

    var label_list = makeOptionsList(
        labels,
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
    var html = `
    <form method='post' action='' class='js-modal-form' enctype='multipart/form-data'>
        <div class='form-group'>
            <label class='control-label requiredField' for='id_label'>
            {% trans "Select Label" %}
            </label>
            <div class='controls'>
                <select id='id_label' class='select form-control name='label'>
                    ${label_list}
                </select>
            </div>
        </div>
    </form>`;

    openModal({
        modal: modal,
    });
    
    modalEnable(modal, true);
    modalSetTitle(modal, '{% trans "Select Label Template" %}');
    modalSetContent(modal, html);
}