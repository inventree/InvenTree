---
title: BOM Export
---

## Exporting BOM Data


BOM data can be exported for any given assembly by selecting the *Export BOM* action from the BOM actions menu.

You will be presented with the *Export BOM* options dialog, shown below:

{% with id="bom_export", url="build/bom_export.png", description="Export BOM Data" %}
{% include 'img.html' %}
{% endwith %}

### BOM Export Options

**Format**

Select the file format for the exported BOM data

**Multi Level BOM**

If selected, BOM data will be included for any subassemblies. If not selected, only top level (flat) BOM data will be exported.

**Levels**

Define the maximum level of data to export for subassemblies. If set to zero, all levels of subassembly data will be exported.

**Include Parameter Data**

Include part parameter data in the exported dataset.

**Include Stock Data**

Include part stock level information in the exported dataset.

**Include Manufacturer Data**

Include part manufacturer information in the exported dataset.

**Include Supplier Data**

Include part supplier information in the exported dataset.
