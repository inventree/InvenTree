{% load inventree_extras %}

/* exported
    editSettings,
    user_settings,
    global_settings,
*/

{% user_settings request.user as USER_SETTINGS %}
const user_settings = {
    {% for key, value in USER_SETTINGS.items %}
    {{ key }}: {% primitive_to_javascript value %},
    {% endfor %}
};

{% global_settings as GLOBAL_SETTINGS %}
const global_settings = {
    {% for key, value in GLOBAL_SETTINGS.items %}
    {{ key }}: {% primitive_to_javascript value %},
    {% endfor %}
};

/*
 * Edit a setting value
 */
function editSetting(pk, options={}) {

    // Is this a global setting or a user setting?
    var global = options.global || false;

    var url = '';

    if (global) {
        url = `/api/settings/global/${pk}/`;
    } else {
        url = `/api/settings/user/${pk}/`;
    }

    // First, read the settings object from the server
    inventreeGet(url, {}, {
        success: function(response) {
            
            // Construct the field 
            var fields = {
                value: {
                    label: response.name,
                    help_text: response.description,
                    type: response.type,
                    choices: response.choices,
                }
            };

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

                    if (response.type == 'boolean') {
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
