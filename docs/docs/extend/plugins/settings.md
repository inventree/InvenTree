---
title: Settings Mixin
---

## SettingsMixin

The *SettingsMixin* allows the plugin to save and load persistent settings to the database.

- Plugin settings are stored against the individual plugin, and thus do not have to be unique
- Plugin settings are stored using a "key:value" pair

Use the class constant `SETTINGS` for a dict of settings that should be added as global database settings.

The dict must be formatted similar to the following sample that shows how to use validator choices and default.

Take a look at the settings defined in `InvenTree.common.models.InvenTreeSetting` for all possible parameters.

### Example

Below is a simple example of how a plugin can implement settings:

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
            'required': True,
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

!!! info "More Info"
    For more information on any of the methods described below, refer to the InvenTree source code.

!!! tip "Hidden Settings"
    Plugin settings can be hidden from the settings page by marking them as 'hidden'

This mixin defines the helper functions `plugin.get_setting`, `plugin.set_setting` and `plugin.check_settings` to access all plugin specific settings. The `plugin.check_settings` function can be used to check if all settings marked with `'required': True` are defined and not equal to `''`. Note that these methods cannot be used in the `__init__` function of your plugin.

```python
api_url = self.get_setting('API_URL', cache = False)
self.set_setting('API_URL', 'some value')
is_valid, missing_settings = self.check_settings()
```
`get_setting` has an additional parameter which lets control if the value is taken directly from the database or from the cache. If it is left away `False` is the default that means the value is taken directly from the database.
