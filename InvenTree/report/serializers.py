
from InvenTree.serializers import InvenTreeModelSerializer
from InvenTree.serializers import InvenTreeAttachmentSerializerField

from .models import TestReport
from .models import BuildReport
from .models import BillOfMaterialsReport
from .models import PurchaseOrderReport, SalesOrderReport


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
