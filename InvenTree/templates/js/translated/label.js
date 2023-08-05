{% load i18n %}
{% load static %}
{% load inventree_extras %}
/* globals
    attachSelect,
    closeModal,
    inventreeGet,
    makeOptionsList,
    modalEnable,
    modalSetContent,
    modalSetTitle,
    modalShowSubmitButton,
    modalSubmit,
    openModal,
    showAlertDialog,
    showMessage,
    user_settings,
*/

/* exported
    printLabels,
*/

/**
 * Present the user with the available labels,
 * and allow them to select which label to print.
 *
 * The intent is that the available labels have been requested
 * (via AJAX) from the server.
 */
function selectLabel(labels, items, options={}) {
    // Array of available plugins for label printing
    var plugins = [];

    // Request a list of available label printing plugins from the server
    inventreeGet(
        `/api/plugins/`,
        {
            mixin: 'labels',
        },
        {
            async: false,
            success: function(response) {
                plugins = response;
            }
        }
    );

    var plugin_selection = '';

    if (plugins.length > 0) {
        plugin_selection =`
        <div class='form-group'>
            <label class='control-label requiredField' for='id_plugin'>
            {% trans "Select Printer" %}
            </label>
            <div class='controls'>
                <select id='id_plugin' class='select form-control' name='plugin'>
        `;

        plugins.forEach(function(plugin) {
            var selected = '';
            if (user_settings['LABEL_DEFAULT_PRINTER'] == plugin.key) {
                selected = ' selected';
            }
            plugin_selection += `<option value='${plugin.key}' title='${plugin.meta.human_name}'${selected}>${plugin.name} - <small>${plugin.meta.human_name}</small></option>`;
        });

        plugin_selection += `
                    </select>
                </div>
            </div>
        `;
    }

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
        },
        null,
        function(item) {
            if (options.key == 'part')
                return item.pk == user_settings.DEFAULT_PART_LABEL_TEMPLATE;
            else if (options.key == 'location')
                return item.pk == user_settings.DEFAULT_LOCATION_LABEL_TEMPLATE;
            else if (options.key == 'item')
                return item.pk == user_settings.DEFAULT_ITEM_LABEL_TEMPLATE;
            return '';
        }
    );

    // Construct form
    var html = '';

    if (items.length > 0) {
        let item_name = items.length == 1 ? options.singular_name : options.plural_name;
        html += `
        <div class='alert alert-block alert-info'>
        ${items.length} ${item_name} {% trans "selected" %}
        </div>`;
    }

    html += `
    <form method='post' action='' class='js-modal-form' enctype='multipart/form-data'>
        <div class='form-group'>
            <label class='control-label requiredField' for='id_label'>
            {% trans "Select Label Template" %}
            </label>
            <div class='controls'>
                <select id='id_label' class='select form-control' name='label'>
                    ${label_list}
                </select>
            </div>
        </div>
        ${plugin_selection}
    </form>`;

    openModal({
        modal: modal,
    });

    modalEnable(modal, true);
    modalShowSubmitButton(modal, true);
    modalSetTitle(modal, '{% trans "Select Label Template" %}');
    modalSetContent(modal, html);

    attachSelect(modal);

    modalSubmit(modal, function() {

        var label = $(modal).find('#id_label').val();
        var plugin = $(modal).find('#id_plugin').val();

        closeModal(modal);

        if (options.success) {
            options.success({
                // Return the selected label template and plugin
                label: label,
                plugin: plugin,
            });
        }
    });
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
 */
function printLabels(options) {

    if (!options.items || options.items.length == 0) {
        showAlertDialog(
            '{% trans "Select Items" %}',
            '{% trans "No items selected for printing" %}',
        );
        return;
    }

    let params = {
        enabled: true,
    };

    params[options.key] = options.items;

    // Request a list of available label templates
    inventreeGet(options.url, params, {
        success: function(response) {
            if (response.length == 0) {
                showAlertDialog(
                    '{% trans "No Labels Found" %}',
                    '{% trans "No label templates found which match the selected items" %}',
                );
                return;
            }

            // Select label template for printing
            selectLabel(response, options.items, {
                success: function(data) {
                    let href = `${options.url}${data.label}/print/?`;

                    options.items.forEach(function(item) {
                        href += `${options.key}=${item}&`;
                    });

                    href += `plugin=${data.plugin}`;

                    inventreeGet(href, {}, {
                        success: function(response) {
                            if (response.file) {
                                // Download the generated file
                                window.open(response.file);
                            } else {
                                showMessage('{% trans "Labels sent to printer" %}', {
                                    style: 'success',
                                });
                            }
                        }
                    });
                },
                plural_name: options.plural_name,
                singular_name: options.singular_name,
                key: options.key,
            });
        }
    });
}
