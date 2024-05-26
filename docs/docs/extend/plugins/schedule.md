---
title: Schedule Mixin
---

## ScheduleMixin

The ScheduleMixin class provides a plugin with the ability to call functions at regular intervals.

- Functions are registered with the InvenTree worker which runs as a background process.
- Scheduled functions do not accept any arguments
- Plugin member functions can be called
- Global functions can be specified using dotted notation

!!! tip "Enable Schedule Integration"
    The *Enable Schedule Integration* option but be enabled, for scheduled plugin events to be activated.

{% with id="schedule", url="plugin/enable_schedule.png", description="Enable schedule integration" %}
{% include 'img.html' %}
{% endwith %}

### SamplePlugin

An example of a plugin which supports scheduled tasks:

::: plugin.samples.integration.scheduled_task.ScheduledTaskPlugin
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []
