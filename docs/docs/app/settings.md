---
title: App Settings
---

## Settings

The *Settings* view provides access to user configurable settings, in addition to information about the app itself.

The main settings view is shown below, and provides the following options:

- **Server** - Configure and select server profile
- **App Settings** - Configure app settings
- **Home Screen** - Configure home screen settings
- **Part** - Configure part settings
- **About** - Display  app version information

{% with id="settings_view", url="app/settings.png", maxheight="240px", description="Settings view" %}
{% include 'img.html' %}
{% endwith %}

## App Settings

The *App Settings* view provides configuration options for the InvenTree app:

{% with id="app_settings", url="app/app_settings.png", maxheight="240px", description="App Settings" %}
{% include 'img.html' %}
{% endwith %}

### Parts

Configure options for "parts" display:

- **Include Subcategories** - When viewing a list of parts in a category, include parts from subcategories

### Stock

Configure options for "stock" display:

- **Include Sublocations** - When viewing a list of stock items in a location, include items from sublocations
- **Stock History** - Display stock item history in the stock detail view

### Sounds

Configure audible app notifications:

- **Server Error** - Play an audible tone when a server error occurs
- **Barcode Tones** - Play audible tones when scanning barcodes

### App Settings

- **Dark Mode** - Enable "dark mode" display for the app.
- **Use Strict HTTPS** - Enforce strict checking of HTTPs certificates. Enabling this option may prevent you from connecting to the server if there are certificate issues.
- **Language** - Select app language. By default, will use the system language of the device the app is installed on.
- **Upload Error Reports** - Enable uploading of anonymous error / crash reports. These reports are used to improve the quality of the app.

## Home Screen

The *Home Screen* view allows you to configure display options for the app 'home screen':

{% with id="home_settings", url="app/home_settings.png", maxheight="240px", description="Home Screen Settings" %}
{% include 'img.html' %}
{% endwith %}
