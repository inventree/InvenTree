# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.serializers import InvenTreeModelSerializer
from InvenTree.serializers import InvenTreeAttachmentSerializerField

from .models import TestReport
from .models import BuildReport
from .models import BillOfMaterialsReport


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
