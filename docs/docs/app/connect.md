---
title: Connect to Server
---

## Connect to InvenTree

Use of the InvenTree app assumes that you (the user) have access to an InvenTree server.

When first running the app, no profile has been configured. The *server* icon in the top-right corner of the home screen is <span style='color: red'>red</span>, indicating that there is no connection to an InvenTree server:

{% with id="no_server", url="app/initial.png", maxheight="240px", description="No server configured" %}
{% include "img.html" %}
{% endwith %}

Press on the server icon to navigate to the server selection view:

{% with id="no_profiles", url="app/no_profiles.png", maxheight="240px", description="No server configured" %}
{% include "img.html" %}
{% endwith %}


### Create Server

!!! success "Server Profiles"
    The app supports multiple server profiles, providing simple switching between different InvenTree servers and/or account profiles.

Press the <span class='fas fa-plus-circle blue'></span> button in the bottom-right corner of the screen to create a new server profile.

{% with id="add_profile", url="app/add_server_profile.png", maxheight="240px", description="Add server" %}
{% include 'img.html' %}
{% endwith %}

Enter the required server details:

| Parameter | Description |
| --- | --- |
| **Name** | Name for the server profile (can be any value, simply for reference) |
| **Server** | InvenTree server address (including port, if required). e.g. `http://inventree.myserver.com:8080` |
| **Username** | Your account username (case sensitive) |
| **Password** | Your account password (case sensitive) |

### Connect to Server

Once the server profile is created, you need to connect to the server. Simply short press on the server profile to connect.

Alternatively, long press on the server profile to activate the context menu, then select *Connect to Server*.

When the app successfully connects to the server, a success message is briefly displayed at the bottom of the screen. A green <span class='fas fa-check-circle green'></span> icon next to the server profile indicate that the profile is currently *selected* and also the connection was successful.

{% with id="connected", url="app/connected.png", maxheight="240px", description="Connected to server" %}
{% include 'img.html' %}
{% endwith %}

### Connection Failure

If (for whatever reason) the app does not successfully connect to the InvenTree server, a failure message is displayed, and a red <span class='fas fa-times-circle red'></span> icon is displayed next to the server profile.

{% with id="failed", url="app/unauthorized.png", maxheight="240px", description="Connection failure" %}
{% include 'img.html' %}
{% endwith %}

In this case, the error message displayed at the bottom of the screen provides context as to why the app could not successfully connect to the server.

To edit the server profile details, long press on the server profile, and select *Edit Server Profile*:

{% with id="edit", url="app/edit_server.png", maxheight="240px", description="Edit server profile" %}
{% include 'img.html' %}
{% endwith %}
