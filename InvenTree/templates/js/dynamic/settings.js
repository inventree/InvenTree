{% load inventree_extras %}

/* exported
    editSetting,
    user_settings,
    global_settings,
    plugins_enabled,
*/

{% user_settings request.user as USER_SETTINGS %}
const user_settings = {
    {% for key, value in USER_SETTINGS.items %}
    {{ key }}: {% primitive_to_javascript value %},
    {% endfor %}
};

{% visible_global_settings as GLOBAL_SETTINGS %}
const global_settings = {
    {% for key, value in GLOBAL_SETTINGS.items %}
    {{ key }}: {% primitive_to_javascript value %},
    {% endfor %}
};

{% plugins_enabled as p_en %}
{% if p_en %}
const plugins_enabled = true;
{% else %}
const plugins_enabled = false;
{% endif %}

/*
 * Interactively edit a setting value.
 * Launches a modal dialog form to adjut the value of the setting.
 */
function editSetting(key, options={}) {

    // Is this a global setting or a user setting?
    var global = options.global || false;
    var plugin = options.plugin;
    var notification = options.notification;
    var connection_key = options.connection_key;
    var connection = options.connection;

    var url = '';

    if (connection_key) {
        url = `/api/plugin/settings/${plugin}/connection/${connection_key}/${connection}/${key}/`;
    } else if (plugin) {
        url = `/api/plugin/settings/${plugin}/${key}/`;
    } else if (notification) {
        url = `/api/settings/notification/${pk}/`;
    } else if (global) {
        url = `/api/settings/global/${key}/`;
    } else {
        url = `/api/settings/user/${key}/`;
    }

    var reload_required = false;

    // First, read the settings object from the server
    inventreeGet(url, {}, {
        success: function(response) {

            if (response.choices && response.choices.length > 0) {
                response.type = 'choice';
                reload_required = true;
            }

            // Construct the field
            var fields = {
                value: {
                    label: response.name,
                    help_text: response.description,
                    type: response.type,
                    choices: response.choices,
                    value: response.value,
                }
            };

            // Foreign key lookup available!
            if (response.type == 'related field') {

                if (response.model_name && response.api_url) {
                    fields.value.type = 'related field';
                    fields.value.model = response.model_name.split('.').at(-1);
                    fields.value.api_url = response.api_url;
                } else {
                    // Unknown / unsupported model type, default to 'text' field
                    fields.value.type = 'text';
                    console.warn(`Unsupported model type: '${response.model_name}' for setting '${response.key}'`);
                }
            }

            constructChangeForm(fields, {
                url: url,
                method: 'PATCH',
                title: options.title,
                processResults: function(data, fields, opts) {

                    switch (data.type) {
                    case 'boolean':
                        // Convert to boolean value
                        data.value = data.value.toString().toLowerCase() == 'true';
                        break;
                    case 'integer':
                        // Convert to integer value
                        data.value = parseInt(data.value.toString());
                        break;
                    default:
                        break;
                    }

                    return data;
                },
                processBeforeUpload: function(data) {
                    // Convert value to string
                    data.value = data.value.toString();

                    return data;
                },
                onSuccess: function(response) {

                    var setting = response.key;

                    if (reload_required) {
                        location.reload();
                    } else if (response.type == 'boolean') {
                        var enabled = response.value.toString().toLowerCase() == 'true';
                        $(`#setting-value-${setting}`).prop('checked', enabled);
                    } else {
                        $(`#setting-value-${setting}`).html(response.value);
                    }
                }
            });
        },
        error: function(xhr) {
            showApiError(xhr, url);
        }
    });
}
