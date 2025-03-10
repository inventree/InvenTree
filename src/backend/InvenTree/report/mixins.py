"""Report mixin classes."""

from django.db import models


class InvenTreeReportMixin(models.Model):
    """A mixin class for adding report generation functionality to a model class.

    In addition to exposing the model to the report generation interface,
    this mixin provides a hook for providing extra context information to the reports.
    """

    class Meta:
        """Metaclass options for this mixin."""

        abstract = True

    def report_context(self) -> dict:
        """Generate a dict of context data to provide to the reporting framework.

        The default implementation returns an empty dict object.
        """
        return {}
