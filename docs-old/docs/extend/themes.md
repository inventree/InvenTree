---
title: Changing color theme
---

## Color Themes

You can customize the look of InvenTree via the color themes feature.

### Select Color Theme

Navigate to the "Settings" page and click on the "Display" tab, you should see the following:

{% with id="theme_default", url="settings/theme_default.png", description="Default InvenTree color theme" %}
{% include 'img.html' %}
{% endwith %}

The drop-down list let's you select any other color theme found in your static folder (see next section to find out how to [add color themes](#add-color-themes)). Once selected, click on the "Apply Theme" button for the new color theme to be activated.

!!! info "Per-user Setting"
	Color themes are "user specific" which means that changing the color theme in your own settings won't affect other users.

Here is an example what the "Dark Reader" theme looks like:

{% with id="theme_dark", url="settings/theme_dark.png", description="Dark Reader InvenTree color theme" %}
{% include 'img.html' %}
{% endwith %}

### Add Color Theme

#### Local Installation
To add a color theme, you'll need to add a new CSS sheet in your static folder (the default folder is located at `{{ static_folder_local_default }}css/color-themes/`).

InvenTree automatically lists all CSS sheets found in the `{{ static_folder_local_default }}css/color-themes/` folder and present them inside the dropdown list on the "Settings > Theme" page.

#### InvenTree Source Code

If you would like a CSS sheet to be permanently added to InvenTree's source code so that other users can benefit too, add it to the `{{ static_folder_source }}css/color-themes/` folder then submit a pull request.
