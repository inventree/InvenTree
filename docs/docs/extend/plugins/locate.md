---
title: Locate Mixin
---

## LocateMixin

The `LocateMixin` class enables plugins to "locate" stock items (or stock locations) via an entirely custom method.

For example, a warehouse could be arranged with each individual 'parts bin' having an audio-visual indicator (e.g. RGB LED and buzzer). "Locating" a particular stock item causes the LED to flash and the buzzer to sound.

Another example might be a parts retrieval system, where "locating" a stock item causes the stock item to be "delivered" to the user via a conveyor.

The possibilities are endless!

### Web Integration

{% with id="web_locate", url="plugin/web_locate.png", description="Locate stock item from web interface", maxheight="400px" %}
{% include 'img.html' %}
{% endwith %}

### App Integration

If a locate plugin is installed and activated, the [InvenTree mobile app](../../app/app.md) displays a button for locating a StockItem or StockLocation (see below):

{% with id="app_locate", url="plugin/app_locate.png", description="Locate stock item from app", maxheight="400px" %}
{% include 'img.html' %}
{% endwith %}

### Implementation

Refer to the [InvenTree source code](https://github.com/inventree/InvenTree/blob/master/InvenTree/plugin/samples/locate/locate_sample.py) for a simple implementation example.
