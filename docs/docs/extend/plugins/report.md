---
title: Report Mixin
---

## ReportMixin

The ReportMixin class provides a plugin with the ability to extend the functionality of custom [report templates](../../report/report.md). A plugin which implements the ReportMixin mixin class can add custom context data to a report template for rendering.

### Add Report Context

A plugin which implements the ReportMixin mixin can define the `add_report_context` method, allowing custom context data to be added to a report template at time of printing.

### Add Label Context

Additionally the `add_label_context` method, allowing custom context data to be added to a label template at time of printing.

### Example

A sample plugin which provides additional context data to the report templates can be found [in the InvenTree source code](https://github.com/inventree/InvenTree/blob/master/InvenTree/plugin/samples/integration/report_plugin_sample.py):

```python
"""Sample plugin for extending reporting functionality"""

import random

from plugin import InvenTreePlugin
from plugin.mixins import ReportMixin
from report.models import PurchaseOrderReport


class SampleReportPlugin(ReportMixin, InvenTreePlugin):
    """Sample plugin which provides extra context data to a report"""

    NAME = "Sample Report Plugin"
    SLUG = "reportexample"
    TITLE = "Sample Report Plugin"
    DESCRIPTION = "A sample plugin which provides extra context data to a report"
    VERSION = "1.0"

    def some_custom_function(self):
        """Some custom function which is not required for the plugin to function"""
        return random.randint(0, 100)

    def add_report_context(self, report_instance, model_instance, request, context):

        """Add example content to the report instance"""

        # We can add any extra context data we want to the report

        # Generate a random string of data
        context['random_text'] = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=20))

        # Call a custom method
        context['random_int'] = self.some_custom_function()

        # We can also add extra data to the context which is specific to the report type
        context['is_purchase_order'] = isinstance(report_instance, PurchaseOrderReport)

        # We can also use the 'request' object to add extra context data
        context['request_method'] = request.method
```
