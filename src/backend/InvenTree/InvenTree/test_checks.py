"""Tests for the InvenTree system checks."""

from unittest import mock

from django.core import checks
from django.test import SimpleTestCase

from rest_framework.generics import ListAPIView

from InvenTree.checks import (
    MISSING_OUTPUT_OPTIONS_MIXIN,
    MISSING_OUTPUT_OPTIONS_MIXIN_PLUGIN,
    check_optional_field_prefetch,
)
from InvenTree.mixins import OutputOptionsMixin
from order.serializers import SalesOrderShipmentSerializer


class OptionalFieldPrefetchCheckTest(SimpleTestCase):
    """Tests for the check_optional_field_prefetch system check."""

    def test_no_warnings(self):
        """No registered list view may silently ignore OptionalField.prefetch_fields."""
        warnings = check_optional_field_prefetch()

        self.assertEqual(warnings, [], '\n'.join(str(w) for w in warnings))

    def test_detects_missing_mixin(self):
        """A core list view without OutputOptionsMixin is reported as an error."""

        class BadList(ListAPIView):
            serializer_class = SalesOrderShipmentSerializer

        class GoodList(OutputOptionsMixin, ListAPIView):
            serializer_class = SalesOrderShipmentSerializer

        with mock.patch(
            'InvenTree.checks.iter_view_classes', return_value=[BadList, GoodList]
        ):
            errors = check_optional_field_prefetch()

        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], checks.Error)
        self.assertTrue(errors[0].is_serious())
        self.assertEqual(errors[0].id, MISSING_OUTPUT_OPTIONS_MIXIN)
        self.assertIs(errors[0].obj, BadList)
        self.assertIn('order_detail', errors[0].msg)

    def test_external_plugin_view(self):
        """A view defined outside the InvenTree source tree is only a warning."""

        class PluginList(ListAPIView):
            serializer_class = SalesOrderShipmentSerializer

        with (
            mock.patch('InvenTree.checks.iter_view_classes', return_value=[PluginList]),
            mock.patch('InvenTree.checks.is_core_view', return_value=False),
        ):
            errors = check_optional_field_prefetch()

        self.assertEqual(len(errors), 1)
        self.assertNotIsInstance(errors[0], checks.Error)
        self.assertFalse(errors[0].is_serious())
        self.assertEqual(errors[0].id, MISSING_OUTPUT_OPTIONS_MIXIN_PLUGIN)
