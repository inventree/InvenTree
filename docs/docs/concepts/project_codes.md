---
title: Project Codes
---

## Project Codes

A project code is a unique identifier assigned to a specific  project, which helps in tracking and organizing project-related activities and resources. It enables easy retrieval of project-related data and facilitates project management and reporting.

Individual orders (such as [Purchase Orders](../purchasing/purchase_order.md) or [Sales Orders](../sales/sales_order.md)) can be assigned a *Project Code* to allocate the order against a particular internal project.

### Managing Project Codes

Management of project codes (such as creating or editing codes) is accessed via the [settings page](../settings/global.md). Select the *Project Codes* tab to access project code configuration options:

{{ image("settings/project_codes.png", "Project Codes") }}

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("PROJECT_CODES_ENABLED") }}

#### Enable Project Code Support

By default, project code support is disabled. Select the *Enable Project Codes* option to enable support for this feature

## Assigning Project Codes

Project codes can be assigned to an order when the order is created, or at any later stage by simply editing the order. If project code support is enabled, a *Project Code* field is available in the order details form:

{{ image("order/assign_project_code.png", "Assign Project Code") }}

## Filtering by Project Codes

The order tables can be easily filtered or sorted by project code:

{{ image("order/filter_by_project.png", "Filter by Project Code") }}
