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

### Example (all events)

Implementing classes must at least provide a `process_event` function:

```python
class EventPlugin(EventMixin, InvenTreePlugin):
    """
    A simple example plugin which responds to events on the InvenTree server.

    This example simply prints out the event information.
    A more complex plugin could respond to specific events however it wanted.
    """

    NAME = "EventPlugin"
    SLUG = "event"
    TITLE = "Triggered Events"

    def process_event(self, event, *args, **kwargs):
        print(f"Processing triggered event: '{event}'")
```

### Example (specific events)

If you want to process just some specific events, you can also implement the `wants_process_event` function to decide if you want to process this event or not. This function will be executed synchronously, so be aware that it should contain simple logic.

Overall this function can reduce the workload on the background workers significantly since less events are queued to be processed.

```python
class EventPlugin(EventMixin, InvenTreePlugin):
    """
    A simple example plugin which responds to 'salesordershipment.completed' event on the InvenTree server.

    This example simply prints out the event information.
    A more complex plugin can run enhanced logic on this event.
    """

    NAME = "EventPlugin"
    SLUG = "event"
    TITLE = "Triggered Events"

    def wants_process_event(self, event):
        """Here you can decide if this event should be send to `process_event` or not."""
        return event == "salesordershipment.completed"

    def process_event(self, event, *args, **kwargs):
        """Here you can run you'r specific logic."""
        print(f"Sales order was completely shipped: '{args}' '{kwargs}'")
```

### Events

Events are passed through using a string identifier, e.g. `build.completed`

The arguments (and keyword arguments) passed to the receiving function depend entirely on the type of event.

Implementing a response to a particular event requires a working knowledge of the InvenTree code base, especially related to that event being received.
