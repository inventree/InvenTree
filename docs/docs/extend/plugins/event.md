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

## Events

Events are passed through using a string identifier, e.g. `build.completed`

The arguments (and keyword arguments) passed to the receiving function depend entirely on the type of event.

!!! info "Read the Code"
    Implementing a response to a particular event requires a working knowledge of the InvenTree code base, especially related to that event being received. While the *available* events are documented here, to implement a response to a particular event you will need to read the code to understand what data is passed to the event handler.

## Generic Events

There are a number of *generic* events which are generated on certain database actions. Whenever a database object is created, updated, or deleted, a corresponding event is generated.

#### Object Created

When a new object is created in the database, an event is generated with the following event name: `<app>_<model>.created`, where `<model>` is the name of the model class (e.g. `part`, `stockitem`, etc).

The event is called with the following keywords arguments:

- `model`: The model class of the object that was created
- `id`: The primary key of the object that was created

**Example:**

A new `Part` object is created with primary key `123`, resulting in the following event being generated:

```python
trigger_event('part_part.created', model='part', id=123)
```

### Object Updated

When an object is updated in the database, an event is generated with the following event name: `<app>_<model>.saved`, where `<model>` is the name of the model class (e.g. `part`, `stockitem`, etc).

The event is called with the following keywords arguments:

- `model`: The model class of the object that was updated
- `id`: The primary key of the object that was updated

**Example:**

A `Part` object with primary key `123` is updated, resulting in the following event being generated:

```python
trigger_event('part_part.saved', model='part', id=123)
```

### Object Deleted

When an object is deleted from the database, an event is generated with the following event name: `<app>_<model>.deleted`, where `<model>` is the name of the model class (e.g. `part`, `stockitem`, etc).

The event is called with the following keywords arguments:

- `model`: The model class of the object that was deleted
- `id`: The primary key of the object that was deleted (if available)

**Example:**

A `Part` object with primary key `123` is deleted, resulting in the following event being generated:

```python
trigger_event('part_part.deleted', model='part', id=123)
```

!!! warning "Object Deleted"
    Note that the event is triggered *after* the object has been deleted from the database, so the object itself is no longer available.

## Specific Events

In addition to the *generic* events listed above, there are a number of other events which are triggered by *specific* actions within the InvenTree codebase.

The available events are provided in the enumerations listed below. Note that while the names of the events are documented here, the exact arguments passed to the event handler will depend on the specific event being triggered.

### Build Events

::: build.events.BuildEvents
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []

### Part Events

::: part.events.PartEvents
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []

### Stock Events

::: stock.events.StockEvents
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []

### Purchase Order Events

::: order.events.PurchaseOrderEvents
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []

### Sales Order Events

::: order.events.SalesOrderEvents
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []

### Return Order Events

::: order.events.ReturnOrderEvents
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []

### Plugin Events

::: plugin.events.PluginEvents
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []

## Samples

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
