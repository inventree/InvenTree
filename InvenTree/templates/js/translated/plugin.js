{% load i18n %}
{% load inventree_extras %}

/* globals
    constructForm,
*/

/* exported
    installPlugin,
*/

function installPlugin() {
    constructForm(`/api/plugin/install/`, {
        method: 'POST',
        title: '{% trans "Install Plugin" %}',
        fields: {
            url: {},
            packagename: {},
            confirm: {},
        },
        onSuccess: function(data) {
            msg = '{% trans "The Plugin was installed" %}';
            showMessage(msg, {style: 'success', details: data.result, timeout: 30000});
        }
    });
}