---
title: App Navigation
---


## Home Screen

The app *home screen* provides quick-access buttons for stock view and actions:

{% with id="home", url="app/home.png", maxheight="240px", description="Home screen" %}
{% include 'img.html' %}
{% endwith %}

## Tab Display

Some screens provide multiple tabbed views, which are displayed at the top of the screen:

{% with id="global_nav", url="app/app_tabs.png", maxheight="240px", description="App tabs" %}
{% include 'img.html' %}
{% endwith %}

Tabs can be navigated by pressing on the text of each tab, or by scrolling the screen left or right.

## Global Actions

The *Global Action* buttons are visible on most screens, displayed in the bottom left corner of the screen:

{% with id="global_nav", url="app/app_global_navigation.png", maxheight="240px", description="Global navigation actions" %}
{% include 'img.html' %}
{% endwith %}

### Open Drawer Menu

The <span class='fas fa-list'></span> action opens the *Drawer Menu*, which is a quick-access menu for global navigation:

{% with id="drawer", url="app/drawer.png", maxheight="240px", description="Open drawer menu" %}
{% include 'img.html' %}
{% endwith %}

The *Drawer Menu* can be accessed in the following ways:

- From the *Home Screen* select the *Drawer* icon in the top-left corner of the screen
- From any other screen, long-press the *Back* button in the top-left corner of the screen

### Search

The <span class='fas fa-search'></span> action opens the [Search](./search.md) screen

### Scan Barcode

The <span class='fas fa-qrcode'></span> action opens the [barcode scan](./barcode.md#global-scan) window, which allows quick access to the barcode scanning functionality.

## Context Actions

Within a given view, certain context actions may be available. If there are contextual actions which can be performed, they are displayed in the bottom right corner:

{% with id="drawer", url="app/context_actions.png", maxheight="240px", description="Context actions" %}
{% include 'img.html' %}
{% endwith %}

!!! tip "Barcode Actions"
    Available barcode actions are displayed in a separate context action menu
