---
title: App Mixin
---

## AppMixin

If this mixin is added to a plugin the directory the plugin class is defined in is added to the list of `INSTALLED_APPS` in the InvenTree server configuration.

!!! warning "Danger Zone"
    Only use this mixin if you have an understanding of djangos [app system]({% include "django.html" %}/ref/applications). Plugins with this mixin are deeply integrated into InvenTree and can cause difficult to reproduce or long-running errors. Use the built-in testing functions of django to make sure your code does not cause unwanted behaviour in InvenTree before releasing.
