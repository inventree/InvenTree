{% load i18n %}
{% load static %}
{% load inventree_extras %}
/* globals
    attachSelect,
    closeModal,
    constructForm,
    getFormFieldValue,
    inventreeGet,
    makeOptionsList,
    modalEnable,
    modalSetContent,
    modalSetTitle,
    modalShowSubmitButton,
    modalSubmit,
    openModal,
    showAlertDialog,
    showApiError,
    showMessage,
    updateForm,
    user_settings,
*/

/* exported
    printLabels,
*/


/*
 *  Print label(s) for the selected items:
 *
 * - Retrieve a list of matching label templates from the server
 * - Present the available templates to the user (if more than one available)
 * - Request printed labels
 *
 * Required options:
 * - model_type: The "type" of label template to print against
 * - items: The list of items to be printed
 * - key: The key to use in the query parameters
 * - plural_name: The plural name of the item type
 */
function printLabels(options) {

    let plugin_name = '';

    if (!options.items || options.items.length == 0) {
        showAlertDialog(
            '{% trans "Select Items" %}',
            '{% trans "No items selected for printing" %}',
        );
        return;
    }

    // Join the items with a comma character
    const item_string = options.items.join(',');

    let params = {
        enabled: true,
        model_type: options.model_type,
        items: item_string,
    };

    function getPrintingFields(plugin_slug, callback) {

        let url = '{% url "api-label-print" %}' + `?plugin=${plugin_slug}`;

        inventreeGet(
            url,
            {},
            {
                method: 'OPTIONS',
                success: function(response) {
                    let fields = response?.actions?.POST ?? {};
                    callback(fields);
                }
            }
        );
    }

    // Callback when a particular label printing plugin is selected
    function onPluginSelected(value, name, field, formOptions) {

        if (value == plugin_name) {
            return;
        }

        plugin_name = value;

        // Request new printing options for the selected plugin
        getPrintingFields(value, function(fields) {
            formOptions.fields = getFormFields(fields);
            updateForm(formOptions);

            // workaround to fix a bug where one cannot scroll after changing the plugin
            // without opening and closing the select box again manually
            $("#id__plugin").select2("open");
            $("#id__plugin").select2("close");
        });
    }

    const baseFields = {
        template: {},
        plugin: {
            idField: 'key',
        },
        items: {}
    };

    function getFormFields(customFields={}) {
        let fields = {
            ...baseFields,
            ...customFields,
        };

        fields['template'].filters = {
            enabled: true,
            model_type: options.model_type,
            items: item_string,
        };

        fields['plugin'].filters = {
            active: true,
            mixin: 'labels'
        };

        fields['plugin'].onEdit = onPluginSelected;

        fields['items'].hidden = true;
        fields['items'].value = options.items;

        return fields;
    }

    constructForm('{% url "api-label-print" %}', {
        method: 'POST',
        title: '{% trans "Print Label" %}',
        fields: getFormFields(),
        onSuccess: function(response) {
            if (response.complete) {
                if (response.output) {
                    window.open(response.output, '_blank');
                } else {
                    showMessage('{% trans "Labels sent to printer" %}', {
                        style: 'success'
                    });
                }
            } else {
                showMessage('{% trans "Label printing failed" %}', {
                    style: 'warning',
                });
            }
        }
    });
}
