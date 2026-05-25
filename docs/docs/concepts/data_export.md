---
title: Exporting Data
---

## Exporting Data

InvenTree provides data export functionality for a variety of data types. Most data tables in the web interface include a *Download* button in the table toolbar, which allows the currently displayed data to be exported to a file.

!!! info "Filtered Data"
    The export reflects the data currently visible in the table — any active filters, search terms, or sort order are carried through to the exported file. To export the full dataset, clear all filters before exporting.

!!! info "Paginated Data"
    In the user interface, data tables are paginated to improve performance. When exporting data, the export will include **all** records that match the current filters and search terms, not just the records visible on the current page.

## How to Export

**Step 1** — In any table view, click the {{ icon("cloud-download") }} *Download* button in the table toolbar:

{{ image("admin/export.png", "Download button") }}

**Step 2** — An export dialog is displayed. Select the desired *Export Format* and *Export Plugin*, then click *Export*:

{{ image("admin/export_options.png", "Export dialog") }}

**Step 3** — The export runs in the background. A loading indicator is shown while the export is being processed. When the export is complete, the file is automatically downloaded to your browser.

## Supported File Formats

The following file formats are available for export:

| Format | Description |
|--------|-------------|
| CSV | Comma-separated values. Portable plain-text format, compatible with most tools. |
| Excel | Microsoft Excel format (`.xlsx`). Suitable for direct use in spreadsheet applications. |
| TSV | Tab-separated values. Similar to CSV but uses tab characters as delimiters. |

## Export Plugins

InvenTree uses a plugin-based export system. The export dialog lists all plugins that are available for the data type being exported. Selecting a different plugin may provide additional export options or a different output format.

### Built-in Exporters

InvenTree includes the following built-in export plugins:

| Plugin | Description |
|--------|-------------|
| [InvenTree Exporter](../plugins/builtin/inventree_exporter.md) | General-purpose exporter for any tabulated dataset. Always enabled. |
| [BOM Exporter](../plugins/builtin/bom_exporter.md) | Custom exporter for Bill of Materials data, with additional BOM-specific options. |
| [Parameter Exporter](../plugins/builtin/parameter_exporter.md) | Exports part data including all associated custom parameter values as additional columns. |
| [Stocktake Exporter](../plugins/builtin/stocktake_exporter.md) | Exports a comprehensive stock-level summary for parts, with optional pricing and variant data. |

Custom export plugins can also be developed using the [DataExportMixin](../plugins/mixins/export.md).

## API Export

Data can also be exported programmatically via the InvenTree REST API. To trigger an export, perform a `GET` request against any list endpoint with the following query parameters:

| Parameter | Description |
|-----------|-------------|
| `export` | Set to `true` to trigger an export |
| `export_format` | File format: `csv`, `xlsx`, or `tsv` (default: `csv`) |
| `export_plugin` | Slug of the export plugin to use (default: `inventree-exporter`) |

Additional `export_*` parameters may be accepted depending on the plugin selected.

**Example:**

```
GET /api/part/?export=true&export_format=xlsx&export_plugin=inventree-exporter
```

Refer to the [API documentation](../api/index.md) for further details.
