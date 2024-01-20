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
 * - url: The list URL for the particular template type
 * - items: The list of items to be printed
 * - key: The key to use in the query parameters
 * - plural_name: The plural name of the item type
 */
function printLabels(options) {

    if (!options.items || options.items.length == 0) {
        showAlertDialog(
            '{% jstrans "Select Items" %}',
            '{% jstrans "No items selected for printing" %}',
        );
        return;
    }

    let params = {
        enabled: true,
    };

    params[options.key] = options.items;

    // Request a list of available label templates from the server
    let labelTemplates = [];
    inventreeGet(options.url, params, {
        async: false,
        success: function (response) {
            if (response.length == 0) {
                showAlertDialog(
                    '{% jstrans "No Labels Found" %}',
                    '{% jstrans "No label templates found which match the selected items" %}',
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
            ${options.items.length} ${options.plural_name} {% jstrans "selected" %}
            </div>
        `;
    }

    const updateFormUrl = (formOptions) => {
        const plugin = getFormFieldValue("_plugin", formOptions.fields._plugin, formOptions);
        const labelTemplate = getFormFieldValue("_label_template", formOptions.fields._label_template, formOptions);
        const params = $.param({ plugin, [options.key]: options.items })
        formOptions.url = `${options.url}${labelTemplate ?? "1"}/print/?${params}`;
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
                divider: { type: "candy", html: `<hr/><h5>{% jstrans "Printing Options" %}</h5>` },
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
        title: options.items.length === 1 ? `{% jstrans "Print label" %}` : `{% jstrans "Print labels" %}`,
        submitText: `{% jstrans "Print" %}`,
        method: "POST",
        disableSuccessMessage: true,
        header_html,
        fields: {
            _label_template: {
                label: `{% jstrans "Select label template" %}`,
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
                label: `{% jstrans "Select plugin" %}`,
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
            if (response.file) {
                // Download the generated file
                window.open(response.file);
            } else {
                showMessage('{% jstrans "Labels sent to printer" %}', {
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
