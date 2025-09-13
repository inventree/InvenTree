---
title: Supplier Mixin
---

## SupplierMixin

The `SupplierMixin` class enables plugins to integrate with external suppliers, enabling seamless creation of parts, supplier parts, and manufacturer parts with just a few clicks from the supplier. The import process is split into multiple phases:

- Search supplier
- Select InvenTree category
- Match Part Parameters
- Create initial Stock

### Import Methods

When a user initiates a search through the UI, the `get_search_results` function is called, and the search results are returned. These contain a `part_id` which is then passed to `get_import_data` if a user decides to import that specific part. This function should return a bunch of data that is needed for the import process. This data may be cached in the future for the same `part_id`. Then depending if the user only wants to import the supplier and manufacturer part or the whole part, the `import_part`, `import_manufacturer_part` and `import_supplier_part` methods are called automatically. If the user has imported the complete part, the `get_parameters` method is used to get a list of parameters which then can be match to inventree part parameter templates with some provided guidance. Additionally the `get_pricing_data` method is used to extract price breaks which are automatically considered when creating initial stock through the UI in the part import wizard.

For that to work, a few methods need to be overridden:

::: plugin.base.supplier.mixins.SupplierMixin
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      summary: False
      members:
        - get_search_results
        - get_import_data
        - get_pricing_data
        - get_parameters
        - import_part
        - import_manufacturer_part
        - import_supplier_part
      extra:
        show_sources: True

### Sample Plugin

A simple example is provided in the InvenTree code base. Note that this uses some static data, but this can be extended in a real world plugin to e.g. call the supplier's API:

::: plugin.samples.supplier.supplier_sample.SampleSupplierPlugin
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []
