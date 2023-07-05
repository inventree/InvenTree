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

### Example

Implementing classes must provide a `process_event` function:

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

### Events

Events are passed through using a string identifier, e.g. `build.completed`

The arguments (and keyword arguments) passed to the receiving function depend entirely on the type of event.

Implementing a response to a particular event requires a working knowledge of the InvenTree code base, especially related to that event being received.
