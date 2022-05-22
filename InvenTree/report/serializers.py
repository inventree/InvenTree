
from InvenTree.serializers import (InvenTreeAttachmentSerializerField,
                                   InvenTreeModelSerializer)

from .models import (BillOfMaterialsReport, BuildReport, PurchaseOrderReport,
                     SalesOrderReport, TestReport)


class TestReportSerializer(InvenTreeModelSerializer):

    template = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
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

    template = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
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

    template = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
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

    template = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
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

    template = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        model = SalesOrderReport
        fields = [
            'pk',
            'name',
            'description',
            'template',
            'filters',
            'enabled',
        ]
