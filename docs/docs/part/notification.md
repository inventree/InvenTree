---
title: Part Notifications
---

## Part Notification Events

Multiple events can trigger [notifications](../concepts/notifications.md) related to *Parts* in InvenTree. These notifications can be delivered via the user interface, email, or third-party integrations.

### Low Stock Notification

If the *minimum stock* threshold is set for a *Part*, then a "low stock" notification can be generated when the stock level for that part falls below the configured level.

Any users who are subscribed to notifications for the part in question will receive a low stock notification via email.

### Build Order Notification

When a new [Build Order](../manufacturing/build.md) is created, the InvenTree software checks to see if any of the parts required to complete the order are low on stock.

If there are any parts with low stock, a notification is generated for any users subscribed to notifications for the part being built.

## Subscribing to Notifications

Users can "subscribe" to either a *Part* or *Part Category*, to receive notifications.

### Part

When subscribed to a *Part*, a user will receive notifications when events occur which pertain to:

- That particular part
- Any parts which are variants of that part

If a user is subscribed to a particular part, it will be indicated as shown below:

{% with id="part_sub_on", url="part/part_subscribe_on.png", description="Subscribe" %}
{% include 'img.html' %}
{% endwith %}

If the user is not subscribed, the subscription icon is greyed out, as shown here:

{% with id="part_sub_off", url="part/part_subscribe_off.png", description="Subscribe" %}
{% include 'img.html' %}
{% endwith %}

Clicking on this icon will toggle the subscription status for this part.

### Part Category

When subscribed to a *Part Category*, a user will receive notifications when particular events occur which pertain to:

- That particular category
- Any sub-categories at lower levels
- Any parts contained in the category
- Any parts contained in the lower level categories

Subscribing to a part category operates in the same manner as for a part - simply click on the notification icon.
