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

const defaultLabelTemplates = {
    part: user_settings.DEFAULT_PART_LABEL_TEMPLATE,
    location: user_settings.DEFAULT_LOCATION_LABEL_TEMPLATE,
    item: user_settings.DEFAULT_ITEM_LABEL_TEMPLATE,
    line: user_settings.DEFAULT_LINE_LABEL_TEMPLATE,
}


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

    constructForm('{% url "api-label-print" %}', {
        method: 'POST',
        title: '{% trans "Print Label" %}',
        fields: {
            template: {
                filters: {
                    enabled: true,
                    model_type: options.model_type,
                    items: item_string,
                }
            },
            plugin: {
                filters: {
                    active: true,
                    mixin: 'labels',
                }
            },
            items: {
                hidden: true,
                value: options.items
            }
        },
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

    return;

    // Request a list of available label templates from the server
    let labelTemplates = [];
    inventreeGet('{% url "api-label-template-list" %}', params, {
        async: false,
        success: function (response) {
            if (response.length == 0) {
                showAlertDialog(
                    '{% trans "No Labels Found" %}',
                    '{% trans "No label templates found which match the selected items" %}',
                );
                return;
            }

            labelTemplates = response;
        }
    });

    // Request a list of available label printing plugins from the server
    let plugins = [];
    inventreeGet(`/api/plugins/`, { mixin: 'labels' }, {
        async: false,
        success: function (response) {
            plugins = response;
        }
    });

    let header_html = "";

    // show how much items are selected if there is more than one item selected
    if (options.items.length > 1) {
        header_html += `
            <div class='alert alert-block alert-info'>
            ${options.items.length} ${options.plural_name} {% trans "selected" %}
            </div>
        `;
    }

    const updateFormUrl = (formOptions) => {
        const plugin = getFormFieldValue("_plugin", formOptions.fields._plugin, formOptions);
        const labelTemplate = getFormFieldValue("_label_template", formOptions.fields._label_template, formOptions);
        const params = $.param({ plugin, items: item_string })
        formOptions.url = `{% url "api-label-template-list" %}${labelTemplate ?? "1"}/print/?${params}`;
    }

    const updatePrintingOptions = (formOptions) => {
        let printingOptionsRes = null;
        $.ajax({
            url: formOptions.url,
            type: "OPTIONS",
            contentType: "application/json",
            dataType: "json",
            accepts: { json: "application/json" },
            async: false,
            success: (res) => { printingOptionsRes = res },
            error: (xhr) => showApiError(xhr, formOptions.url)
        });

        const printingOptions = printingOptionsRes.actions.POST || {};

        // clear all other options
        formOptions.fields = {
            _label_template: formOptions.fields._label_template,
            _plugin: formOptions.fields._plugin,
        }

        if (Object.keys(printingOptions).length > 0) {
            formOptions.fields = {
                ...formOptions.fields,
                divider: { type: "candy", html: `<hr/><h5>{% trans "Printing Options" %}</h5>` },
                ...printingOptions,
            };
        }

        // update form
        updateForm(formOptions);

        // workaround to fix a bug where one cannot scroll after changing the plugin
        // without opening and closing the select box again manually
        $("#id__plugin").select2("open");
        $("#id__plugin").select2("close");
    }

    const printingFormOptions = {
        title: options.items.length === 1 ? `{% trans "Print label" %}` : `{% trans "Print labels" %}`,
        submitText: `{% trans "Print" %}`,
        method: "POST",
        disableSuccessMessage: true,
        header_html,
        fields: {
            _label_template: {
                label: `{% trans "Select label template" %}`,
                type: "choice",
                localOnly: true,
                value: defaultLabelTemplates[options.key],
                choices: labelTemplates.map(t => ({
                    value: t.pk,
                    display_name: `${t.name} - <small>${t.description}</small>`,
                })),
                onEdit: (_value, _name, _field, formOptions) => {
                    updateFormUrl(formOptions);
                }
            },
            _plugin: {
                label: `{% trans "Select plugin" %}`,
                type: "choice",
                localOnly: true,
                value: user_settings.LABEL_DEFAULT_PRINTER || plugins[0].key,
                choices: plugins.map(p => ({
                    value: p.key,
                    display_name: `${p.name} - <small>${p.meta.human_name}</small>`,
                })),
                onEdit: (_value, _name, _field, formOptions) => {
                    updateFormUrl(formOptions);
                    updatePrintingOptions(formOptions);
                }
            },
        },
        onSuccess: (response) => {
            let output = response.output ?? response.file;
            if (output) {
                // Download the generated file
                window.open(output, '_blank');
            } else {
                showMessage('{% trans "Labels sent to printer" %}', {
                    style: 'success',
                });
            }
        }
    };

    // construct form
    constructForm(null, printingFormOptions);

    // fetch the options for the default plugin
    updateFormUrl(printingFormOptions);
    updatePrintingOptions(printingFormOptions);
}
