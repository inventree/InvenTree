---
title: Schedule Mixin
---

## ScheduleMixin

The ScheduleMixin class provides a plugin with the ability to call functions at regular intervals.

- Functions are registered with the InvenTree worker which runs as a background process.
- Scheduled functions do not accept any arguments
- Plugin member functions can be called
- Global functions can be specified using dotted notation

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
