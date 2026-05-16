---
title: Slack Notification Plugin
---

## Slack Notification Plugin

This plugin provides a mechanism to send notifications to a Slack channel when certain events occur in InvenTree. It implements the [NotificationMixin](../mixins/notification.md) mixin class, allowing it to send notifications based on events defined in the InvenTree system.

### API Key

To use this plugin, you need to provide a Slack API key. This key is used to authenticate the plugin with the Slack API and send messages to the specified channel.

### Activation

This plugin is an *optional* plugin, and must be enabled in the InvenTree settings.
