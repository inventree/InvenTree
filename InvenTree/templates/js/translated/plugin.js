{% load i18n %}
{% load inventree_extras %}

/* globals
    constructForm,
*/

/* exported
    installPlugin,
    locateItemOrLocation,
    loadSupplierApiTable,
*/

function installPlugin() {
    constructForm(`/api/plugin/install/`, {
        method: 'POST',
        title: '{% trans "Install Plugin" %}',
        fields: {
            packagename: {},
            url: {},
            confirm: {},
        },
        onSuccess: function(data) {
            msg = '{% trans "The Plugin was installed" %}';
            showMessage(msg, {style: 'success', details: data.result, timeout: 30000});
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
        `/api/plugin/`,
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

/*
 * Load table displaying list of supplier parts
 */
function loadSupplierApiTable(table, options) {
    options.params = options.params || {};
    var filters = loadTableFilters('supplier-api');
    for (var key in options.params) {
        filters[key] = options.params[key];
    }

    $(table).inventreeTable({
        url: options.url,
        queryParams: filters,
        name: 'supplier-api',
        groupBy: false,
        sidePagination: 'server',
        original: options.params,
        formatNoMatches: function() {
            return '{% trans "No matching parts for this supplier found" %}';
        },
        onRefresh: function() {loadSupplierApiTable(table, options);},
        columns: [
            {
                title: '',
                checkbox: true,
                visible: true,
                switchable: false,
            },
            {
                sortable: true,
                field: 'id',
                title: '{% trans "Supplier ID" %}',
            },
            {
                sortable: true,
                field: 'title',
                title: '{% trans "Title" %}',
            },
            {
                sortable: false,
                field: 'description',
                title: '{% trans "Description" %}',
            },
            {
                sortable: false,
                field: 'link',
                title: '{% trans "Link" %}',
            },
        ],
    });
}
