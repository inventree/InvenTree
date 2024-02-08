---
title: Interactive API
---

## Interactive API

If the server is running in [Debug Mode](../start/intro.md#debug-mode) then an interactive version of the API is available using a browser.

!!! info "Debug Mode"
    This interactive API is only available when running the server in debug mode

!!! warning "Slow Traffic Ahead"
    The interactive API is *significantly* slower than using the normal JSON format. It is provided only for development and testing.

### List View

Various list endpoints can be displayed as shown below:

{% with id="api_browse", url="api/api_browse.png", description="List API" %}
{% include 'img.html' %}
{% endwith %}

### Filtering

List views can be filtered interactively:

{% with id="api_filter", url="api/api_filters.png", description="Filter API" %}
{% include 'img.html' %}
{% endwith %}

### Detail View

Detail view endpoints can also be displayed:

{% with id="api_detail", url="api/api_detail.png", description="Detail API" %}
{% include 'img.html' %}
{% endwith %}
