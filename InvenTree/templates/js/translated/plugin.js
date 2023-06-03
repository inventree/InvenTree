{% load i18n %}
{% load inventree_extras %}

/* globals
    constructForm,
    showMessage,
    inventreeGet,
    inventreePut,
*/

/* exported
    installPlugin,
    activatePlugin,
    locateItemOrLocation
*/

function installPlugin() {
    constructForm(`/api/plugins/install/`, {
        method: 'POST',
        title: '{% trans "Install Plugin" %}',
        fields: {
            packagename: {},
            url: {},
            confirm: {},
        },
        onSuccess: function(data) {
            let msg = '{% trans "The Plugin was installed" %}';
            showMessage(msg, {style: 'success', details: data.result, timeout: 30000});
        }
    });
}


/*
 * Activate a specific plugin via the API
 */
function activatePlugin(plugin_id) {

    let url = `{% url "api-plugin-list" %}${plugin_id}/activate/`;

    let html = `
    <span class='alert alert-block alert-info'>
    {% trans "Are you sure you want to activate this plugin?" %}
    </span>
    `;

    constructForm(null, {
        title: '{% trans "Activate Plugin" %}',
        preFormContent: html,
        confirm: true,
        submitText: '{% trans "Activate" %}',
        onSubmit: function(_fields, opts) {
            showModalSpinner(opts.modal);

            inventreePut(
                url,
                {},
                {
                    method: 'PATCH',
                    success: function() {
                        $(opts.modal).modal('hide');
                        addCachedAlert('{% trans "Plugin activated" %}', {style: 'success'});
                        location.reload();
                    },
                    error: function(xhr) {
                        $(opts.modal).modal('hide');
                        showApiError(xhr, url);
                    }
                }
            )
        }
    });
}


function locateItemOrLocation(options={}) {

    if (!options.item && !options.location) {
        console.error(`locateItemOrLocation: Either 'item' or 'location' must be provided!`);
        return;
    }

    function performLocate(plugin) {
        inventreePut(
            '{% url "api-locate-plugin" %}',
            {
                plugin: plugin,
                item: options.item,
                location: options.location,
            },
            {
                method: 'POST',
            },
        );
    }

    // Request the list of available 'locate' plugins
    inventreeGet(
        `/api/plugins/`,
        {
            mixin: 'locate',
        },
        {
            success: function(plugins) {
                // No 'locate' plugins are available!
                if (plugins.length == 0) {
                    console.warn(`No 'locate' plugins are available`);
                } else if (plugins.length == 1) {
                    // Only a single locate plugin is available
                    performLocate(plugins[0].key);
                } else {
                    // More than 1 location plugin available
                    // Select from a list
                }
            }
        },
    );
}
