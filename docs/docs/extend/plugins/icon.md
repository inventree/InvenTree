---
title: Icon Pack Mixin
---

## IconPackMixin

The IconPackMixin class provides basic functionality for letting plugins expose custom icon packs that are available in the InvenTree UI. This is especially useful to provide a custom crafted icon pack with icons for different location types, e.g. different sizes and styles of drawers, bags, ESD bags, ... which are not available in the standard tabler icons library.

### Sample Plugin

The following example demonstrates how to use the `IconPackMixin` class to add a custom icon pack:

::: plugin.samples.icons.icon_sample.SampleIconPlugin
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []
