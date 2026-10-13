"""Business context references retain original API permissions and exact identity."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from .assistant_references import validate_references
from .test_assistant_tools import ReceiptToolFixture


class AssistantReferenceTests(ReceiptToolFixture, TestCase):
    """Exercise existing native purchase records using only fictional fixtures."""

    def setUp(self):
        """Create an operator with existing purchase rights and a native receipt."""
        self.build_fixture()

    def test_reference_resolves_original_record_and_rechecks_rights(self):
        """Labels and URLs originate from the server, with no grant prerequisite."""
        reference = {'object_type': 'purchase_order', 'object_id': str(self.order.pk)}
        resolved = validate_references(self.user, [reference])
        self.assertEqual(resolved[0]['object_id'], str(self.order.pk))
        self.assertIn(self.order.reference, resolved[0]['label'])
        self.assertEqual(
            resolved[0]['page_url'], f'/purchasing/purchase-order/{self.order.pk}/'
        )
        self.user.groups.clear()
        with self.assertRaises(PermissionDenied):
            validate_references(self.user, resolved)

    def test_unknown_duplicate_wildcard_and_missing_records_are_rejected(self):
        """No arbitrary paths, nonexistent objects or ambiguous selections enter context."""
        reference = {'object_type': 'purchase_order', 'object_id': str(self.order.pk)}
        for references in (
            [reference, reference],
            [{'object_type': 'user', 'object_id': '1'}],
            [{'object_type': 'purchase_order', 'object_id': '*'}],
            [{'object_type': 'purchase_order', 'object_id': '999999999'}],
            [reference] * 9,
        ):
            with (
                self.subTest(references=references),
                self.assertRaises(ValidationError),
            ):
                validate_references(self.user, references)
