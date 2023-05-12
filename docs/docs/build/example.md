---
title: Build Order Example
---

## Build Order Example

For example, let's say we wish to create 10 new "Widgets". We create a new build for the widget, which signals an *intent* to assemble the "Widget" in quantity 10. As the *Widget* is a serialized part, with tracked subcomponents, the build outputs must themselves be serialized. This means that we need to generate 10 separate build outputs for this build order.

#### Create Build Order

First, create a new build order for the *Widget* assembly:

{% with id="build_example_create", url="build/build_example_create.png", description="Create build output" %}
{% include "img.html" %}
{% endwith %}
