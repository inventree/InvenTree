---
title: Importing Data from suppliers
---

## Import data from suppliers

InvenTree can integrate with external suppliers and import data from them, which helps to setup your system. Currently parts, supplier parts and manufacturer parts can be created automatically.

### Requirements

1. Install a supplier mixin plugin for you supplier
2. Goto "Admin Center > Plugins > [The supplier plugin]" and set the supplier company setting. Some plugins may require additional settings like API tokens.

### Import a part

New parts can be imported from the _Part Category_ view, by pressing the _Import Part_ button:

{{ image("part/import_part.png", "Import part") }}

Then just follow the wizard to confirm the category, select the parameters and create initial stock.

{{ image("part/import_part_wizard.png", "Import part wizard") }}

### Import a supplier part

If you already have the part created, you can also just import the supplier part with it's corresponding manufacturer part. Open the supplier panel for the part and use the "Import supplier part" button:

{{ image("part/import_supplier_part.png", "Import supplier part") }}
