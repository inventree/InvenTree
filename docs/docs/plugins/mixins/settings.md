---
title: Settings Mixin
---

## SettingsMixin

The *SettingsMixin* allows the plugin to save and load persistent settings to the database.

- Plugin settings are stored against the individual plugin, and thus do not have to be unique
- Plugin settings are stored using a "key:value" pair

## Plugin Settings

Use the class attribute `SETTINGS` for a dict of settings that should be added as global database settings.

The dict must be formatted similar to the following sample that shows how to use validator choices and default.

Take a look at the settings defined in `InvenTree.common.models.InvenTreeSetting` for all possible parameters.

### get_setting

Use the `get_setting` method to retrieve a setting value based on the provided key.

::: plugin.base.integration.SettingsMixin.SettingsMixin.get_setting
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      summary: False
      members: []

### set_setting

Use the `set_setting` method to set a value for a specific setting key.

::: plugin.base.integration.SettingsMixin.SettingsMixin.set_setting
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      summary: False
      members: []

## User Settings

Plugins may also define user-specific settings, which allow users to customize the behavior of the plugin on a per-user basis.

To add user-specific settings, use the `USER_SETTINGS` class attribute in a similar way to the `SETTINGS` attribute.

### get_user_setting

Use the `get_user_setting` method to retrieve a user-specific setting value based on the provided key and user.

::: plugin.base.integration.SettingsMixin.SettingsMixin.get_user_setting
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      summary: False
      members: []

### set_user_setting

Use the `set_user_setting` method to set a value for a specific user setting key.

::: plugin.base.integration.SettingsMixin.SettingsMixin.set_user_setting
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      summary: False
      members: []

## Example Plugin

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
            'description': _('Describe me here'),
            'default': 6,
            'validator': [
                int,
                MinValueValidator(2),
                MaxValueValidator(25)
            ]
        },
        'ASSEMBLY': {
            'name': _('Assembled Part'),
            'description': _('Settings can point to internal database models'),
            'model': 'part.part',
            'model_filters': {
                'active': True,
                'assembly': True
            }
        },
        'GROUP': {
            'name': _('User Group'),
            'description': _('Select a group of users'),
            'model': 'auth.group'
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
