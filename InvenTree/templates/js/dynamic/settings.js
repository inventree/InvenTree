{% load inventree_extras %}
// InvenTree settings

var user_settings = {
    {% for key, value in user_settings.items %}
    {{ key }}: {% primitive_to_javascript value %},
    {% endfor %}
};

var global_settings = {
    {% for key, value in global_settings.items %}
    {{ key }}: {% primitive_to_javascript value %},
    {% endfor %}
};