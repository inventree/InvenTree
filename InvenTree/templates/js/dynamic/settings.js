{% load inventree_extras %}
// InvenTree settings

{% user_settings request.user as USER_SETTINGS %}

var user_settings = {
    {% for key, value in USER_SETTINGS.items %}
    {{ key }}: {% primitive_to_javascript value %},
    {% endfor %}
};

{% global_settings as GLOBAL_SETTINGS %}

var global_settings = {
    {% for key, value in GLOBAL_SETTINGS.items %}
    {{ key }}: {% primitive_to_javascript value %},
    {% endfor %}
};