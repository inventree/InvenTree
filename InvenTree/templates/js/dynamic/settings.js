{% load inventree_extras %}

/* exported
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

