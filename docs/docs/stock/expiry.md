---
title: Stock Expiry
---

## Stock Expiry

InvenTree supports stock expiration dates, which allows individual stock items to be automatically marked as *expired* past a certain calendar date.

The stock expiry feature is disabled by default, and must be enabled using the {{ globalsetting("STOCK_ENABLE_EXPIRY", short=True) }} setting:

{{ image("stock/enable_stock_expiry.png", title="Enable stock expiry feature") }}

While the stock expiry feature is disabled, expiry dates are hidden from the stock forms and tables, and expired stock is not treated any differently to other stock.

!!! info "Non Expiring Stock"
    If a stock item is not expected to expire, leave its expiry date blank.

### Add Expiry Date

When creating a new stock item, the expiry date can be manually set by the user. If the part has a [default expiry time](#part-expiry-time), the expiry date is pre-filled accordingly.

{{ image("stock/expiry_date_create.png", title="Add expiry date") }}

When [receiving items](../purchasing/purchase_order.md) against a purchase order, an expiry date can optionally be specified for each received line item (also pre-filled from the default expiry time of the part).

The expiry date can be adjusted in the stock item edit form.

{{ image("stock/expiry_date_edit.png", title="Edit expiry date") }}

### Expired and Stale Stock

A stock item is:

- **Expired** - if its expiry date has passed
- **Stale** - if its expiry date is approaching, within the number of days specified by the {{ globalsetting("STOCK_STALE_DAYS", short=True) }} setting

The stock item detail page displays an *Expired* or *Stale* badge where applicable, along with the expiry date of the stock item:

{{ image("stock/item_expired.png", title="Display expiry date") }}

### Filter Expired Stock

Stock item tables display a column for the expiry date of each stock item, and can be filtered by *Expired* and *Stale* status (or by a range of expiry dates).

{{ image("stock/stock_table_expiry.png", title="Filter by stock expiry") }}

### Dashboard

The *Expired Stock Items* and *Stale Stock Items* [dashboard](../concepts/ui/index.md#dashboard) widgets show the number of expired (and stale) stock items, providing visibility of expired stock to users.

### Using Expired Stock

If the stock expiry feature is enabled, expired stock cannot be allocated to [build orders](../manufacturing/allocate.md) or [sales orders](../sales/sales_order.md) - whether manually, by serial number, or by auto-allocation. This can be changed with the following settings:

| Setting | Description |
| --- | --- |
| {{ globalsetting("STOCK_ALLOW_EXPIRED_BUILD", short=True) }} | Allow expired stock to be allocated to build orders |
| {{ globalsetting("STOCK_ALLOW_EXPIRED_SALE", short=True) }} | Allow expired stock to be allocated to sales orders |

{{ image("stock/sell_build_expired_stock.png", title="Sell and build expired stock") }}

Existing allocations are not affected if the allocated stock expires (or if these settings are changed).

!!! info "Stock Availability"
    Expired stock is still counted as *in stock* - refer to the [stock availability](./availability.md) documentation.

## Part Expiry Time

In addition to allowing manual configuration of expiry dates on a per-item basis, InvenTree also provides the ability to set a "default expiry time" for a particular Part. This expiry time (specified in *days*) is then used to automatically calculate the expiry date when creating a new Stock Item as an instance of the given Part.

For example, if a Part has a default expiry time of 30 days, then any Stock Items created for that Part will automatically have their expiry date set to 30 days in the future (unless an expiry date is specified).

!!! info "Non Expiring Parts"
    If a part is not expected to expire, set the default expiry time to 0 (zero) days.

If a Part has a non-zero default expiry time, it will be displayed on the Part details page

{{ image("stock/part_expiry_display.png", title="Display part expiry") }}

The Part expiry time can be altered using the Part editing form.

{{ image("stock/part_expiry.png", title="Edit part expiry") }}

## Stale Stock Notifications

InvenTree can automatically notify users when stock items are approaching their expiry dates. This feature helps prevent stock from expiring unnoticed by providing advance warning.

### Configuration

The stale stock notification system uses the {{ globalsetting("STOCK_STALE_DAYS", short=True) }} setting to determine when to send notifications. Any in-stock item with an expiry date earlier than this number of days in the future is included - this includes stock items which have *already* expired.

For example, if {{ globalsetting("STOCK_STALE_DAYS", short=True) }} is set to 10, stock items which expire within the next 10 days (and any stock items which have already expired) will be included in the notifications.

### How It Works

The system runs a daily background task that:

1. **Checks for stale stock**: Identifies stock items with expiry dates within the configured threshold
2. **Groups by user**: Organizes stale items by users who are subscribed to notifications for the relevant parts
3. **Sends consolidated emails**: Each user receives a single email containing all their stale stock items

### Prerequisites

For stale stock notifications to work:

1. **Stock expiry must be enabled**: The {{ globalsetting("STOCK_ENABLE_EXPIRY", short=True) }} setting must be enabled
2. **Stale days configured**: The {{ globalsetting("STOCK_STALE_DAYS", short=True) }} setting must be greater than 0
3. **Email configuration**: [Email settings](../settings/email.md) must be properly configured
4. **User subscriptions**: Users must be subscribed to notifications for the relevant parts

### User Subscriptions

Users will only receive notifications for parts they are subscribed to. To subscribe to part notifications:

1. Navigate to the part detail page
2. Click the notification bell icon to subscribe
3. Users can also subscribe to entire part categories

For more information on part subscriptions, see the [Part Notifications](../part/notification.md) documentation.
