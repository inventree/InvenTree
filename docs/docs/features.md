---
title: Features
---

## InvenTree

InvenTree is an open-source inventory management system which provides intuitive parts management and stock control.


It is designed to be lightweight and easy to use for SME or hobbyist applications, where many existing stock management solutions are bloated and cumbersome to use. However, powerful business logic works in the background to ensure that stock tracking history is maintained, and users have ready access to stock level information. InvenTree is designed to allow for a flexible installation.

InvenTree is a [Python](https://www.python.org/) and [Django](https://www.djangoproject.com/) application which stores data in a relational database, and serves this data to the user(s) via a web browser, and (optionally) can be integrated into custom applications via an API.


## Organize Parts

Parts are the fundamental element of any inventory. InvenTree groups parts into structured categories which allow you to arrange parts to meet your particular needs.

[Read more...](./part/part.md)

## Manage Suppliers

InvenTree allows you to easily create, modify or delete suppliers and supplier items linked to any part in your inventory.

[Read more...](./order/company.md#suppliers)

## Instant Stock Knowledge

Instantly view current stock for a certain part, in a particular location, or required for an individual build. Stock items are organized in cascading locations and sub-locations, allowing flexible inspection of stock under any location. Stock items can be serialized for tracking of individual items, and test results can be stored against a serialized stock item for the purpose of acceptance testing and commissioning.

[Read more...](./stock/stock.md)

## BOM Management

Intelligent BOM (Bill of Material) management provides a clear understanding of the sub-parts required to make a new part.
InvenTree allows you to upload simple BOM files in multiple formats, and download a detailed BOM with all the information stored in its database.

[Read more...](./build/bom.md)

## Build Parts

Inventree features a build management system to help you track the progress of your builds.
Builds consume stock items to make new parts, you can decide to automatically or manually allocate parts from your current inventory.

[Read more...](./build/build.md)

## Report

Generate a wide range of reports using custom templates. [Read more...](./report/report.md)

## API

The core InvenTree software is implemented on top of a RESTful API, which can be used by external applications. Additionally, a native Python binding library is provided, for rapid development of programs to integrate with InvenTree.

[Read more...](./api/api.md)

## Extend and Customize

InvenTree is designed to be highly extensible. If the core InvenTree functionality does not meet your particular need, InvenTree provides a powerful plugin system which can be used to extend on base functions as required.

[Read more...](./extend/plugins.md)
