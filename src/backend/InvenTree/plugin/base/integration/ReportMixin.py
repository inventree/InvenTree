"""Plugin mixin class for ReportContextMixin."""


class ReportMixin:
    """Mixin which provides additional context to generated reports.

    This plugin mixin acts as a "shim" when generating reports,
    can can add extra context data to a report template.

    Useful for custom report generation where the report template
    needs some extra information which is not provided by default,
    or some complex logic to generate the report.
    """

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'ReportContext'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('report', True, __class__)

    def add_report_context(self, report_instance, model_instance, request, context):
        """Add extra context to the provided report instance.

        By default, this method does nothing.

        Args:
            report_instance: The report instance to add context to
            model_instance: The model instance which initiated the report generation
            request: The request object which initiated the report generation
            context: The context dictionary to add to
        """
        pass

    def add_label_context(self, label_instance, model_instance, request, context):
        """Add extra context to the provided label instance.

        By default, this method does nothing.

        Args:
            label_instance: The label instance to add context to
            model_instance: The model instance which initiated the label generation
            request: The request object which initiated the label generation
            context: The context dictionary to add to
        """
        pass
