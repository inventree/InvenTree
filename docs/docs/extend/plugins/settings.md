---
title: Settings Mixin
---

## SettingsMixin

The *SettingsMixin* allows the plugin to save and load persistent settings to the database.

- Plugin settings are stored against the individual plugin, and thus do not have to be unique
- Plugin settings are stored using a "key:value" pair

Use the class constant `SETTINGS` for a dict of settings that should be added as global database settings.

The dict must be formatted similar to the following sample that shows how to use validator choices and default. Take a look at the settings defined in `InvenTree.common.models.InvenTreeSetting` for all possible parameters.


``` python
class PluginWithSettings(SettingsMixin, InvenTreePlugin):

    NAME = "PluginWithSettings"

    SETTINGS = {
        'API_ENABLE': {
            'name': 'API Functionality',
            'description': 'Enable remote API queries',
            'validator': bool,
            'default': True,
        },
        'API_KEY': {
            'name': 'API Key',
            'description': 'Security key for accessing remote API',
            'default': '',
        },
        'API_URL': {
            'name': _('API URL'),
            'description': _('Base URL for remote server'),
            'default': 'http://remote.url/api',
        },
        'CONNECTION': {
            'name': _('Printer Interface'),
            'description': _('Select local or network printer'),
            'choices': [('local','Local printer e.g. USB'),('network','Network printer with IP address')],
            'default': 'local',
        },
        'NUMBER': {
            'name': _('A Name'),
            'description': _('Descripe me here'),
            'default': 6,
            'validator': [
                int,
                MinValueValidator(2),
                MaxValueValidator(25)
            ]
        },
        'HIDDEN_SETTING': {
            'name': _('Hidden Setting'),
            'description': _('This setting is hidden from the automatically generated plugin settings page'),
            'hidden': True,
        }
    }
```

This mixin defines the helper functions `plugin.get_setting` and `plugin.set_setting` to access all plugin specific settings:

```python
api_url = self.get_setting('API_URL', cache = False)
self.set_setting('API_URL', 'some value')
```
`get_setting` has an additional parameter which lets control if the value is taken directly from the database or from the cache. If it is left away `False` ist the default that means the value is taken directly from the database.
