---
title: User Settings
---

## User Settings

The various user settings described below can be configured for an individual user, to provide an InvenTree user experienced customized to their preferences. Your user settings can be accessed by selecting *Settings* from the menu in the top right order of the screen.

### Account Settings

The *Account Settings* screen shows configuration options for your user account, including linking [third party logins](./SSO.md) and [multi factor authentication](./MFA.md):

{% with id="user-account", url="settings/user_account.png", description="User Account Settings" %}
{% include 'img.html' %}
{% endwith %}

### Display Settings

The *Display Settings* screen shows general display configuration options. Additionally, this screen allows the user to select the primary language in which InvenTree is displayed.

{% with id="user-display", url="settings/user_display.png", description="User Display Settings" %}
{% include 'img.html' %}
{% endwith %}

### Home Page

This screen allows the user to customize display of items on the InvenTree home page.

{% with id="user-home", url="settings/user_home.png", description="Home Page Settings" %}
{% include 'img.html' %}
{% endwith %}

### Search Settings

Customize settings for search results:

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ usersetting("SEARCH_WHOLE") }}
{{ usersetting("SEARCH_REGEX") }}
{{ usersetting("SEARCH_PREVIEW_RESULTS") }}
{{ usersetting("SEARCH_PREVIEW_SHOW_PARTS") }}
{{ usersetting("SEARCH_HIDE_INACTIVE_PARTS") }}
{{ usersetting("SEARCH_PREVIEW_SHOW_SUPPLIER_PARTS") }}
{{ usersetting("SEARCH_PREVIEW_SHOW_MANUFACTURER_PARTS") }}
{{ usersetting("SEARCH_PREVIEW_SHOW_CATEGORIES") }}
{{ usersetting("SEARCH_PREVIEW_SHOW_STOCK") }}
{{ usersetting("SEARCH_PREVIEW_HIDE_UNAVAILABLE_STOCK") }}
{{ usersetting("SEARCH_PREVIEW_SHOW_LOCATIONS") }}
{{ usersetting("SEARCH_PREVIEW_SHOW_COMPANIES") }}
{{ usersetting("SEARCH_PREVIEW_SHOW_BUILD_ORDERS") }}
{{ usersetting("SEARCH_PREVIEW_SHOW_PURCHASE_ORDERS") }}
{{ usersetting("SEARCH_PREVIEW_EXCLUDE_INACTIVE_PURCHASE_ORDERS") }}
{{ usersetting("SEARCH_PREVIEW_SHOW_SALES_ORDERS") }}
{{ usersetting("SEARCH_PREVIEW_EXCLUDE_INACTIVE_SALES_ORDERS") }}
{{ usersetting("SEARCH_PREVIEW_SHOW_RETURN_ORDERS") }}
{{ usersetting("SEARCH_PREVIEW_EXCLUDE_INACTIVE_RETURN_ORDERS") }}

### Notifications

Settings related to notification messages:

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ usersetting("NOTIFICATION_ERROR_REPORT") }}

### Reporting

Settings for label printing and report generation:

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ usersetting("REPORT_INLINE") }}
{{ usersetting("LABEL_INLINE") }}
{{ usersetting("LABEL_DEFAULT_PRINTER") }}
