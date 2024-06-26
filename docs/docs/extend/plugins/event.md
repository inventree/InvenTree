---
title: Event Mixin
---

## EventMixin

The `EventMixin` class enables plugins to respond to certain triggered events.

When a certain (server-side) event occurs, the background worker passes the event information to any plugins which inherit from the `EventMixin` base class.

!!! tip "Enable Event Integration"
    The *Enable Event Integration* option must first be enabled to allow plugins to respond to events.

{% with id="events", url="plugin/enable_events.png", description="Enable event integration" %}
{% include 'img.html' %}
{% endwith %}

### Sample Plugin - All events

Implementing classes must at least provide a `process_event` function:

::: plugin.samples.event.event_sample.EventPluginSample
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []

### Sample Plugin - Specific Events

If you want to process just some specific events, you can also implement the `wants_process_event` function to decide if you want to process this event or not. This function will be executed synchronously, so be aware that it should contain simple logic.

Overall this function can reduce the workload on the background workers significantly since less events are queued to be processed.

::: plugin.samples.event.filtered_event_sample.FilteredEventPluginSample
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []


## Events

Events are passed through using a string identifier, e.g. `build.completed`

The arguments (and keyword arguments) passed to the receiving function depend entirely on the type of event.

Implementing a response to a particular event requires a working knowledge of the InvenTree code base, especially related to that event being received.
