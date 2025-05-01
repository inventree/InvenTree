---
title: Build Order Example
---

## Build Order Example

For example, let's say we wish to create 10 new "Widgets". We create a new build for the widget, which signals an *intent* to assemble the "Widget" in quantity 10. As the *Widget* is a serialized part, with tracked sub-components, the build outputs must themselves be serialized. This means that we need to generate 10 separate build outputs for this build order.

### Create Build Order

First, create a new build order for the *Widget* assembly:

{{ image("build/build_example_create.png", "Create Build Order") }}

### Generate Build Outputs

Generate build outputs for this build order. As this is a tracked item, with tracked sub-components, the build outputs must be serialized:

{{ image("build/build_example_create_outputs.png", "Create Build Outputs") }}

A list of new build outputs will have now been generated:

{{ image("build/build_example_incomplete_list.png", "Incomplete Build Outputs") }}

### Allocate Untracked Stock

Untracked stock items are allocated to the build order in the *Allocate Stock* tab:

{{ image("build/build_example_allocate_untracked.png", "Allocate Untracked Stock") }}

### Allocate Tracked Stock

Tracked stock items are allocated to individual build outputs:

{{ image("build/build_example_allocate_tracked.png", "Allocate Tracked Stock") }}

### Complete Build Outputs

Mark each build output as complete:

{{ image("build/build_example_complete_outputs.png", "Complete Build Outputs") }}

### Complete Build Order

Once the build outputs have been completed, and all stock has been allocated, the build order can be completed.
