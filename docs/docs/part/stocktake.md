---
title: Part Stocktake
---

## Part Stocktake

InvenTree can record the historical stock levels of parts, allowing users to view past stocktake data and generate reports based on this information.

A *Stocktake* refers to a "snapshot" of stock levels for a particular part, at a specific point in time. Stocktake information is used for tracking a historical record of the quantity and value of part stock.

In particular, an individual *Stocktake* record tracks the following information:

- The date of the Stocktake event
- A reference to the [part](./index.md) which is being counted
- The total number of individual [stock items](../stock/index.md) available
- The total stock quantity of available stock
- The total value range of stock on hand

### Stock Items vs Stock Quantity

*Stock Items* refers to the number of stock entries (e.g. *"3 reels of capacitors"*). *Stock Quantity* refers to the total cumulative stock count (e.g. *"4,560 total capacitors"*).

### Value Range of Stock on Hand

The total value range of stock on hand is calculated based on the provided pricing data. For stock items which have a recorded *cost* (e.g. *purchase price*), this value is used. If no direct pricing information is available for a particular stock item, the price range of the part itself is used.

!!! info "Value Range"
    Value data is provided as a *range* of values, accounting for any variability in available pricing data.

### Display Historical Stock Data

Historical stock data for a particular part can be viewed in the *Stock History* tab, available on the *Part* page.

This tab displays a chart of historical stock quantity and cost data, and corresponding tabulated data:

{{ image("part/part_stocktake_tab.png", "Part stocktake tab") }}

If this tab is not visible, ensure that the *Enable Stock History* [user setting](../settings/user.md) is enabled in the *Display Settings* section.

{{ image("part/part_stocktake_enable_tab.png", "Enable stock history tab") }}

### Stocktake Entry Generation

By default, stocktake entries are generated automatically at regular intervals (see [settings](#stock-history-settings) below). However, users can generate a stocktake entry on demand, using the *Generate Stocktake Entry* button in the *Stock History* tab:

{{ image("part/part_stocktake_manual.png", "Generate stocktake entry") }}

This will schedule the generation of a new stocktake entry for the selected part, and the new entry will be visible in the stock history data once the generation process is complete.

## Stocktake Reports

In addition to the part stocktake entries, which are periodically generated for all parts in the database, users can also generate a stocktake *report*, against a particular set of input parameters. Instead of generating a stocktake entry for a single part, this process generates a report which contains stocktake data for all parts which match the specified parameters.

The generated report (once completed) will be available for download as a CSV file, and will contain the stocktake entry data for all parts which match the specified parameters.

### Report Options

The following parameters can be specified when generating a stocktake report:

| Parameter | Description |
| --------- | ----------- |
| Part | If provided, the report will only include stocktake data for the specified part, including and variant parts. If left blank, the report will include data for all parts in the database. |
| Category | If provided, the report will only include stocktake data for parts which belong to the specified category, including any sub-categories. If left blank, the report will include data for all parts in the database. |
| Location | If provided, the report will only include stocktake data for parts which have stock items located at the specified location, including any sub-locations. If left blank, the report will include data for all parts in the database. |

### Generating a Stocktake Report

The following methods for generating a stocktake report via the user interface are available:

#### Dashboard Widget

A dashboard widget is available for generating stocktake reports, which can be added to any dashboard view:

{{ image("part/stocktake_report_dashboard.png", "Stocktake dashboard widget") }}

Here, the user can specify the report parameters, and then click the *Generate Report* button to generate a new stocktake report based on the specified parameters.

## Stocktake Settings

There are a number of configuration options available for controlling the behavior of part stocktake functionality in the [system settings view](../settings/global.md):

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("STOCKTAKE_ENABLE") }}
{{ globalsetting("STOCKTAKE_EXCLUDE_EXTERNAL") }}
{{ globalsetting("STOCKTAKE_AUTO_DAYS") }}
{{ globalsetting("STOCKTAKE_DELETE_OLD_ENTRIES")}}
{{ globalsetting("STOCKTAKE_DELETE_DAYS") }}

{{ image("part/part_stocktake_settings.png", "Stocktake settings") }}

### Enable Stocktake

Enable or disable stocktake functionality. Note that by default, stocktake functionality is disabled.

### Automatic Stocktake Period

Configure the number of days between generation of [automatic stocktake reports](#automatic-stocktake). If this value is set to zero, automatic stocktake reports will not be generated.

### Delete Old Stocktake Entries

If enabled, stocktake entries older than the specified number of days will be automatically deleted from the database.

### Stocktake Deletion Interval

Configure how many days historical stocktake records are retained in the database.
