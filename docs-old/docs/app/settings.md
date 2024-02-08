---
title: App Settings
---

## Settings

The *Settings* view provides access to user configurable settings, in addition to information about the app itself.

The main settings view is shown below, and provides the following options:

| Option | Description |
| --- | --- |
| [Server](./connect.md) | Select server profile and configure settings |
| [App Settings](#app-settings) | Configure app settings |
| [Barcode Settings](#barcode-settings) | Configure barcode scanning settings |
| [Home Screen](#home-screen) | Configure home screen options |
| [Part](#part-settings) | Configure part management options |
| About | Display app version information |


{% with id="settings_view", url="app/settings.png", maxheight="240px", description="Settings view" %}
{% include 'img.html' %}
{% endwith %}

## App Settings

The *App Settings* view provides configuration options for the InvenTree app:

{% with id="app_settings", url="app/app_settings.png", maxheight="240px", description="App Settings" %}
{% include 'img.html' %}
{% endwith %}

### App Settings

| Option | Description |
| --- | --- |
| Dark Mode | Enable "dark mode" display for the app. |
| Screen Orientation | Select [screen orientation mode](#screen-orientation) |
| Use Strict HTTPS | Enforce strict checking of HTTPs certificates. Enabling this option may prevent you from connecting to the server if there are certificate issues. |
| Language | Select app language. By default, will use the system language of the device the app is installed on. |
| Upload Error Reports | Enable uploading of anonymous error / crash reports. These reports are used to improve the quality of the app. |

#### Screen Orientation

By default, the screen orientation follows your system preference. However if desired, the screen orientation can be locked in either portrait or landscape mode.

### Sounds

Configure audible app notifications:

| Option | Description |
| --- | --- |
| Server Error | Play an audible tone when a server error occurs |
| Barcode Tones | Play audible tones when scanning barcodes |

## Barcode Settings

The *Barcode Settings* view allows you to configure options relating to [barcode scanning](./barcode.md):

{% with id="barcode_settings", url="app/barcode_settings.png", maxheight="240px", description="Barcode Settings" %}
{% include 'img.html' %}
{% endwith %}

| Option | Description |
| --- | --- |
| Scanner Input | Select barcode capture mode |
| Barcode Scan Delay | Delay between successive scans |

## Home Screen

The *Home Screen* view allows you to configure display options for the app 'home screen':

{% with id="home_settings", url="app/home_settings.png", maxheight="240px", description="Home Screen Settings" %}
{% include 'img.html' %}
{% endwith %}

| Option | Description |
| --- | --- |
| Subscribed Parts | Show a list of subscribed parts on the home page |
| Show Purchase Orders | Display a link to purchase orders on the home page |
| Show Suppliers | Display a link to suppliers on the home page |

## Part Settings

The *Part Settings* view allows you to configure various options governing what part features are available:

| Option | Description |
| --- | --- |
| Parameters | Enable display of part parameters in the part detail view |
| BOM | Enable bill of materials display in the part detail view |
| Stock History | Enable display of stock history in the stock detail view |
| Test Results | Enable display of test results in the stock detail view |
