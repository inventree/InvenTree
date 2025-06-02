---
title: Notifications
---

## Notifications System

InvenTree provides a notification system which allows users to receive notifications about various events that occur within the system.

## Notification Types

### User Interface

Notifications are displayed in the user interface. New notifications are announced in the header.
{% with id="notification_header", url="part/notification_header.png", description="One new notification in the header" %}
{% include 'img.html' %}
{% endwith %}

They can be viewed in a flyout.
{% with id="notification_flyout", url="part/notification_flyout.png", description="One new notification in the flyout" %}
{% include 'img.html' %}
{% endwith %}

All current notifications are listed in the inbox.
{% with id="notification_inbox", url="part/notification_inbox.png", description="One new notification in the notification inbox" %}
{% include 'img.html' %}
{% endwith %}

All past notification are listed in the history. They can be deleted one-by-one or all at once from there.
{% with id="notification_history", url="part/notification_history.png", description="One old notification in the notification history" %}
{% include 'img.html' %}
{% endwith %}

### Email

Users can also receive notifications via email. This is particularly useful for important events that require immediate attention.

!!! warning "Email Configuration Required"
    External notifications require correct [email configuration](../start/config.md#email-settings). They also need to be enabled in the settings under notifications`.

!!! warning "Valid Email Address"
    Each user must have a valid email address associated with their account to receive email notifications

### Third-Party Integrations

In addition to the built-in notification system, InvenTree can be integrated with third-party services such as Slack or Discord to send notifications. This allows users to receive real-time updates in their preferred communication channels.

Third party integrations rely on the [plugin system](../plugins/index.md) to provide the necessary functionality.

## Notification Options

The following [global settings](../settings/global.md) control the notification system:

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("NOTIFICATIONS_ENABLE") }}
{{ globalsetting("NOTIFICATIONS_LOW_STOCK") }}
{{ globalsetting("INVENTREE_DELETE_NOTIFICATIONS_DAYS") }}

## Notification Categories

### Part Notifications

There are many types of notifications associated with parts in InvenTree. These notifications can be configured to alert users about various events, such as low stock levels, build orders, and more.

Read the [part notification documentation](../part/notification.md) for more details.
