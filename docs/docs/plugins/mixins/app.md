---
title: App Mixin
---

## AppMixin

If this mixin is added to a plugin the directory the plugin class is defined in is added to the list of `INSTALLED_APPS` in the InvenTree server configuration.

!!! warning "Danger Zone"
    Only use this mixin if you have an understanding of Django's [app system]({% include "django.html" %}/ref/applications). Plugins with this mixin are deeply integrated into InvenTree and can cause difficult to reproduce or long-running errors. Use the built-in testing functions of Django to make sure your code does not cause unwanted behaviour in InvenTree before releasing.

## Custom Models

This mixin allows you to define custom database models within your plugin. These models will be automatically registered with the InvenTree server, and will be available for use within your plugin code.

### Model Permissions

Some database operations within the InvenTree ecosystem may require custom permissions checks - to determine which actions a user can perform against a given model. If your plugin defines custom models, you may need to implement a custom permission check method on your model class.

Each model class can implement a `check_user_permission` classmethod, which will be called by the InvenTree permission system when checking permissions for that model. This method should return `True` if the user has the required permissions, and `False` otherwise.


```python
class MyCustomModel(models.Model):
    # model fields here

    @classmethod
    def check_user_permission(cls, user: User, permission: str) -> bool:
        # custom permission logic here
        return True  # or False
```

!!! warning "Default Permissions"
    By default, if the `check_user_permission` method is not implemented, the InvenTree permission system will return `False` for all permission checks against that model. This is to ensure that no permissions are granted by default, and that the plugin developer must explicitly define the required permissions for their custom models.
