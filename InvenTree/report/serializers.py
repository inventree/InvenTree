"""API serializers for the reporting models"""

from InvenTree.serializers import (InvenTreeAttachmentSerializerField,
                                   InvenTreeModelSerializer)

from .models import (BillOfMaterialsReport, BuildReport, PurchaseOrderReport,
                     SalesOrderReport, TestReport)


class TestReportSerializer(InvenTreeModelSerializer):
    """Serializer class for the TestReport model"""

    template = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        """Metaclass options."""

        model = TestReport
        fields = [
            'pk',
            'name',
            'description',
            'template',
            'filters',
            'enabled',
        ]


class BuildReportSerializer(InvenTreeModelSerializer):
    """Serializer class for the BuildReport model"""

    template = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        """Metaclass options."""

        model = BuildReport
        fields = [
            'pk',
            'name',
            'description',
            'template',
            'filters',
            'enabled',
        ]


class BOMReportSerializer(InvenTreeModelSerializer):
    """Serializer class for the BillOfMaterialsReport model"""
    template = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        """Metaclass options."""

        model = BillOfMaterialsReport
        fields = [
            'pk',
            'name',
            'description',
            'template',
            'filters',
            'enabled',
        ]


class PurchaseOrderReportSerializer(InvenTreeModelSerializer):
    """Serializer class for the PurchaseOrdeReport model"""
    template = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        """Metaclass options."""

        model = PurchaseOrderReport
        fields = [
            'pk',
            'name',
            'description',
            'template',
            'filters',
            'enabled',
        ]


class SalesOrderReportSerializer(InvenTreeModelSerializer):
    """Serializer class for the SalesOrderReport model"""
    template = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        """Metaclass options."""

        model = SalesOrderReport
        fields = [
            'pk',
            'name',
            'description',
            'template',
            'filters',
            'enabled',
        ]
