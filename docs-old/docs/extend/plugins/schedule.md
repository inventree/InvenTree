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

### Example

An example of a plugin which supports scheduled tasks:

```python
class ScheduledTaskPlugin(ScheduleMixin, SettingsMixin, InvenTreePlugin):
    """
    Sample plugin which runs a scheduled task, and provides user configuration.
    """

    NAME = "Scheduled Tasks"
    SLUG = 'schedule'

    SCHEDULED_TASKS = {
        'global': {
            'func': 'some_module.function',
            'schedule': 'H',  # Run every hour
        },
        'member': {
            'func': 'foo',
            'schedule': 'I',  # Minutes
            'minutes': 15,
        },
    }

    SETTINGS = {
        'SECRET': {
            'name': 'A secret',
            'description': 'User configurable value',
        },
    }

    def foo(self):
        """
        This function runs every 15 minutes
        """
        secret_value = self.get_setting('SECRET')
        print(f"foo - SECRET = {secret_value})
```

!!! info "More Info"
    For more information on any of the methods described below, refer to the InvenTree source code. [A working example is available as a starting point](https://github.com/inventree/InvenTree/blob/master/InvenTree/plugin/samples/integration/scheduled_task.py).
