---
title: Custom States
---

## Custom States

Several models within InvenTree support the use of custom states. The custom states are display only - the business logic is not affected by the state.

States can be added in the [Admin Center](../settings/admin.md#admin-center) under the "Custom States" section. Each state has a name, label and a color that are used to display the state in the user interface. Changes to these settings will only be reflected in the user interface after a full reload of the interface.

States need to be assigned to a model, state (for example status on a StockItem) and a logical key - that will be used for business logic. These 3 values combined need to be unique throughout the system.

Custom states can be used in the following models:
- StockItem
- Orders (PurchaseOrder, SalesOrder, ReturnOrder, ReturnOrderLine)
