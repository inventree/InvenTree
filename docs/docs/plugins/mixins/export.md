---
title: Data Export Mixin
---

## DataExportMixin

The `DataExportMixin` class provides a plugin with the ability to customize the data export process. The [InvenTree API](../../api/index.md) provides an integrated method to export a dataset to a tabulated file. The default export process is generic, and simply exports the data presented via the API in a tabulated file format.

Custom data export plugins allow this process to be adjusted:

- Data columns can be added or removed
- Rows can be removed or added
- Custom calculations or annotations can be performed.

### Supported Export Types

Each plugin can dictate which datasets are supported using the `supports_export` method. This allows a plugin to dynamically specify whether it can be selected by the user for a given export session.

::: plugin.base.integration.DataExport.DataExportMixin.supports_export
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        summary: False
        members: []

The default implementation returns `True` for all data types.

### Filename Generation

The `generate_filename` method constructs a filename for the exported file.

::: plugin.base.integration.DataExport.DataExportMixin.generate_filename
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      show_source: True
      summary: False
      members: []

### Adjust Columns

The `update_headers` method allows the plugin to adjust the columns selected to be exported to the file.

::: plugin.base.integration.DataExport.DataExportMixin.update_headers
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      show_source: True
      summary: False
      members: []

### Queryset Filtering

The `filter_queryset` method allows the plugin to provide custom filtering to the database query, before it is exported.

::: plugin.base.integration.DataExport.DataExportMixin.filter_queryset
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      show_source: True
      summary: False
      members: []

### Export Data

The `export_data` method performs the step of transforming a [Django QuerySet]({% include "django.html" %}/ref/models/querysets/) into a dataset which can be processed by the [tablib](https://tablib.readthedocs.io/en/stable/) library.

::: plugin.base.integration.DataExport.DataExportMixin.export_data
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      show_source: True
      summary: False
      members: []

Note that the default implementation simply uses the builtin tabulation functionality of the provided serializer class. In most cases, this will be sufficient.

## Custom Export Options

To provide the user with custom options to control the behavior of the export process *at the time of export*, the plugin can define a custom serializer class.

To enable this feature, define an `ExportOptionsSerializer` attribute on the plugin class which points to a DRF serializer class. Refer to the examples below for more information.

### Builtin Exporter Classes

InvenTree provides the following builtin data exporter classes.

### InvenTreeExporter

A generic exporter class which simply serializes the API output into a data file.

::: plugin.builtin.exporter.inventree_exporter.InvenTreeExporter
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []

### BOM Exporter

A custom exporter which only supports [bill of materials](../../manufacturing/bom.md) exporting.

::: plugin.builtin.exporter.bom_exporter.BomExporterPlugin
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []

## Source Code

The full source code of the `DataExportMixin` class:

{{ includefile("src/backend/InvenTree/plugin/base/integration/DataExport.py", title="DataExportMixin") }}
