{% load inventree_extras %}
// InvenTree settings

{% user_settings request.user as USER_SETTINGS %}
{% global_settings as GLOBAL_SETTINGS %}

var user_settings = {
    {% for setting in USER_SETTINGS %}
    {{ setting.key }}: {{ setting.value|safe }},
    {% endfor %}
};

var global_settings = {
    {% for setting in GLOBAL_SETTINGS %}
    {{ setting.key }}: {{ setting.value|safe }},
    {% endfor %}
};