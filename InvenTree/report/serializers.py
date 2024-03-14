"""API serializers for the reporting models."""

import report.models
from InvenTree.serializers import (
    InvenTreeAttachmentSerializerField,
    InvenTreeModelSerializer,
)


class ReportSerializerBase(InvenTreeModelSerializer):
    """Base class for report serializer."""

    template = InvenTreeAttachmentSerializerField(required=True)

    @staticmethod
    def report_fields():
        """Generic serializer fields for a report template."""
        return [
            'pk',
            'name',
            'description',
            'template',
            'filters',
            'page_size',
            'landscape',
            'enabled',
        ]


class TestReportSerializer(ReportSerializerBase):
    """Serializer class for the TestReport model."""

    class Meta:
        """Metaclass options."""

        model = report.models.TestReport
        fields = ReportSerializerBase.report_fields()


class BuildReportSerializer(ReportSerializerBase):
    """Serializer class for the BuildReport model."""

    class Meta:
        """Metaclass options."""

        model = report.models.BuildReport
        fields = ReportSerializerBase.report_fields()


class BOMReportSerializer(ReportSerializerBase):
    """Serializer class for the BillOfMaterialsReport model."""

    class Meta:
        """Metaclass options."""

        model = report.models.BillOfMaterialsReport
        fields = ReportSerializerBase.report_fields()


class PurchaseOrderReportSerializer(ReportSerializerBase):
    """Serializer class for the PurchaseOrdeReport model."""

    class Meta:
        """Metaclass options."""

        model = report.models.PurchaseOrderReport
        fields = ReportSerializerBase.report_fields()


class SalesOrderReportSerializer(ReportSerializerBase):
    """Serializer class for the SalesOrderReport model."""

    class Meta:
        """Metaclass options."""

        model = report.models.SalesOrderReport
        fields = ReportSerializerBase.report_fields()


class ReturnOrderReportSerializer(ReportSerializerBase):
    """Serializer class for the ReturnOrderReport model."""

    class Meta:
        """Metaclass options."""

        model = report.models.ReturnOrderReport
        fields = ReportSerializerBase.report_fields()


class StockLocationReportSerializer(ReportSerializerBase):
    """Serializer class for the StockLocationReport model."""

    class Meta:
        """Metaclass options."""

        model = report.models.StockLocationReport
        fields = ReportSerializerBase.report_fields()


class ReportSnippetSerializer(InvenTreeModelSerializer):
    """Serializer class for the ReportSnippet model."""

    class Meta:
        """Metaclass options."""

        model = report.models.ReportSnippet

        fields = ['pk', 'snippet', 'description']
