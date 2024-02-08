---
title: Build Order Example
---

## Build Order Example

For example, let's say we wish to create 10 new "Widgets". We create a new build for the widget, which signals an *intent* to assemble the "Widget" in quantity 10. As the *Widget* is a serialized part, with tracked subcomponents, the build outputs must themselves be serialized. This means that we need to generate 10 separate build outputs for this build order.

### Create Build Order

First, create a new build order for the *Widget* assembly:

{% with id="build_example_create", url="build/build_example_create.png", description="Create build order" %}
{% include "img.html" %}
{% endwith %}

### Generate Build Outputs

Generate build outputs for this build order. As this is a tracked item, with tracked subcomponents, the build outputs must be serialized:

{% with id="build_example_create_outputs", url="build/build_example_create_outputs.png", description="Create build outputs" %}
{% include "img.html" %}
{% endwith %}

A list of new build outputs will have now been generated:

{% with id="build_example_incomplete_list", url="build/build_example_incomplete_list.png", description="Incomplete build outputs" %}
{% include "img.html" %}
{% endwith %}

### Allocate Untracked Stock

Untracked stock items are allocated to the build order in the *Allocate Stock* tab:

{% with id="build_example_allocate_untracked", url="build/build_example_allocate_untracked.png", description="Allocated Untracked Stock" %}
{% include "img.html" %}
{% endwith %}

### Allocate Tracked Stock

Tracked stock items are allocated to individual build outputs:

{% with id="build_example_allocate_tracked", url="build/build_example_allocated_tracked.png", description="Allocated Tracked Stock" %}
{% include "img.html" %}
{% endwith %}

### Complete Build Outputs

Mark each build output as complete:

{% with id="build_example_complete_outputs", url="build/build_example_complete_outputs.png", description="Complete Build Outputs" %}
{% include "img.html" %}
{% endwith %}

### Complete Build Order

Once the build outputs have been completed, and all stock has been allocated, the build order can be completed.
