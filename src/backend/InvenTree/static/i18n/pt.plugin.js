


/* globals
    addCachedAlert,
    constructForm,
    showMessage,
    inventreeGet,
    inventreePut,
    loadTableFilters,
    makeIconButton,
    renderDate,
    setupFilterList,
    showApiError,
    showModalSpinner,
    wrapButtons,
*/

/* exported
    activatePlugin,
    installPlugin,
    loadPluginTable,
    locateItemOrLocation,
    reloadPlugins,
*/


/*
 * Load the plugin table
 */
function loadPluginTable(table, options={}) {

    options.params = options.params || {};

    let filters = loadTableFilters('plugins', options.params);

    setupFilterList('plugins', $(table), '#filter-list-plugins');

    $(table).inventreeTable({
        url: '/api/plugins/',
        name: 'plugins',
        original: options.params,
        queryParams: filters,
        sortable: true,
        formatNoMatches: function() {
            return 'Nenhum plug-in encontrado';
        },
        columns: [
            {
                field: 'name',
                title: 'Extensões',
                sortable: true,
                switchable: false,
                formatter: function(value, row) {
                    let html = '';

                    if (!row.is_installed) {
                        html += `<span class='fa fa-question-circle' title='Este plug-in não está mais instalado'></span>`;
                    } else if (row.active) {
                        html += `<span class='fa fa-check-circle icon-green' title='Este plug-in está ativo'></span>`;
                    } else {
                        html += `<span class='fa fa-times-circle icon-red' title ='Este plug-in está instalado mas não está ativo'></span>`;
                    }

                    html += `&nbsp;<span>${value}</span>`;

                    if (row.is_builtin) {
                        html += `<span class='badge bg-success rounded-pill badge-right'>Embutido</span>`;
                    }

                    if (row.is_sample) {
                        html += `<span class='badge bg-info rounded-pill badge-right'>Amostra</span>`;
                    }

                    return html;
                }
            },
            {
                field: 'meta.description',
                title: 'Descrição',
                sortable: false,
                switchable: true,
            },
            {
                field: 'meta.version',
                title: 'Versão',
                formatter: function(value, row) {
                    if (value) {
                        let html = value;

                        if (row.meta.pub_date) {
                            html += `<span class='badge rounded-pill bg-dark float-right'>${renderDate(row.meta.pub_date)}</span>`;
                        }

                        return html;
                    } else {
                        return '-';
                    }
                }
            },
            {
                field: 'meta.author',
                title: 'Autor',
                sortable: false,
            },
            {
                field: 'actions',
                title: '',
                switchable: false,
                sortable: false,
                formatter: function(value, row) {
                    let buttons = '';

                    // Check if custom plugins are enabled for this instance
                    if (options.custom && !row.is_builtin && row.is_installed) {
                        if (row.active) {
                            buttons += makeIconButton('fa-stop-circle icon-red', 'btn-plugin-disable', row.key, 'Desativar Plug-in');
                        } else {
                            buttons += makeIconButton('fa-play-circle icon-green', 'btn-plugin-enable', row.key, 'Habilitar Plug-in');
                        }
                    }

                    return wrapButtons(buttons);
                }
            },
        ]
    });

    if (options.custom) {
        // Callback to activate a plugin
        $(table).on('click', '.btn-plugin-enable', function() {
            let pk = $(this).attr('pk');
            activatePlugin(pk, true);
        });

        // Callback to deactivate a plugin
        $(table).on('click', '.btn-plugin-disable', function() {
            let pk = $(this).attr('pk');
            activatePlugin(pk, false);
        });
    }
}


/*
 * Install a new plugin via the API
 */
function installPlugin() {
    constructForm(`/api/plugins/install/`, {
        method: 'POST',
        title: 'Instalar extensão',
        fields: {
            packagename: {},
            url: {},
            confirm: {},
        },
        onSuccess: function(data) {
            let msg = 'O Plug-in foi instalado';
            showMessage(msg, {style: 'success', details: data.result, timeout: 30000});

            // Reload the plugin table
            $('#table-plugins').bootstrapTable('refresh');
        }
    });
}


/*
 * Activate a specific plugin via the API
 */
function activatePlugin(plugin_id, active=true) {

    let url = `/api/plugins/${plugin_id}/activate/`;

    let html = active ? `
    <span class='alert alert-block alert-info'>
    Tem certeza que deseja habilitar este plug-in?
    </span>
    ` : `
    <span class='alert alert-block alert-danger'>
    Tem certeza que deseja desabilitar este plug-in?
    </span>
    `;

    constructForm(null, {
        title: active ? 'Habilitar Plug-in' : 'Desativar Plug-in',
        preFormContent: html,
        confirm: true,
        submitText: active ? 'Habilitar' : 'Desabilitar',
        submitClass: active ? 'success' : 'danger',
        onSubmit: function(_fields, opts) {
            showModalSpinner(opts.modal);

            inventreePut(
                url,
                {
                    active: active,
                },
                {
                    method: 'PATCH',
                    success: function() {
                        $(opts.modal).modal('hide');
                        addCachedAlert('Plug-in atualizado', {style: 'success'});
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


/*
 * Reload the plugin registry
 */
function reloadPlugins() {
    let url = '/api/plugins/reload/';

    constructForm(url, {
        title: 'Recarregar plugins',
        method: 'POST',
        confirm: true,
        fields: {
            force_reload: {
                // hidden: true,
                value: true,
            },
            full_reload: {
                // hidden: true,
                value: true,
            },
            collect_plugins: {
                // hidden: true,
                value: true,
            },
        },
        onSuccess: function() {
            location.reload();
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
            '/api/locate/',
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
