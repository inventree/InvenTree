"""Report mixin classes."""

from typing import Generic, TypedDict, TypeVar

from django.db import models

_Model = TypeVar('_Model', bound=models.Model, covariant=True)


class QuerySet(Generic[_Model]):
    """A custom QuerySet class used for type hinting in report context definitions.

    This will later be replaced by django.db.models.QuerySet, but as
    django's QuerySet is not a generic class, we need to create our own to not
    loose type data.
    """


class BaseReportContext(TypedDict):
    """Base context for a report model."""


class InvenTreeReportMixin(models.Model):
    """A mixin class for adding report generation functionality to a model class.

    In addition to exposing the model to the report generation interface,
    this mixin provides a hook for providing extra context information to the reports.
    """

    class Meta:
        """Metaclass options for this mixin."""

        abstract = True

    def report_context(self) -> BaseReportContext:
        """Generate a dict of context data to provide to the reporting framework.

        The default implementation returns an empty dict object.

        This method must contain a type annotation, as it is used by the report generation framework
        to determine the type of context data that is provided to the report template.

        Example:
        ```python
        class MyModelReportContext(BaseReportContext):
            my_field: str
            po: order.models.PurchaseOrder
            bom_items: report.mixins.QuerySet[part.models.BomItem]

        class MyModel(report.mixins.InvenTreeReportMixin):
            ...
            def report_context(self) -> MyModelReportContext:
                return {
                    'my_field': self.my_field,
                    'po': self.po,
                }
        ```
        """
        return {}
