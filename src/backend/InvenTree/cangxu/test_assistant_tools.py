"""Real native attachment association under fictional receipt data and scoped authority."""

import os
import tempfile
import uuid
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.test import TestCase, override_settings
from django.utils import timezone

from PIL import Image
from rest_framework.test import APIRequestFactory

from common.models import Attachment
from company.models import Company, SupplierPart
from order.models import PurchaseOrder, PurchaseOrderLineItem
from part.models import Part
from stock.models import StockLocation
from users.models import RuleSet

from .assistant_business_models import ReceiptArchiveEvidence
from .assistant_models import (
    AssistantCommand,
    AssistantGrant,
    AssistantOutboxEvent,
    PartnerBinding,
)
from .assistant_services import CommandConflictError, execute_command
from .assistant_tool_api import AssistantInternalToolsView
from .assistant_tools import LINK_ARCHIVE, receipt_status
from .models import PurchaseReceipt, PurchaseReceiptInspection

DEPLOYMENT = 'b55db895-0d0a-4d42-9c55-7c047130a11e'
SERVICE_TOKEN = 'fictional-assistant-runtime-test-credential'


class ReceiptToolFixture:
    """Create fictional native objects; do not create parallel inventory balances."""

    def build_fixture(self):
        """Prepare a receipt, bounded grant and a real tiny image attachment."""
        self.files = tempfile.TemporaryDirectory(prefix='cangxu-assistant-files-')
        self.addCleanup(self.files.cleanup)
        media = override_settings(MEDIA_ROOT=self.files.name)
        media.enable()
        self.addCleanup(media.disable)
        self.user = get_user_model().objects.create_user(
            username='fictional-archive-operator'
        )
        group = Group.objects.create(name='Fictional archive operators')
        self.user.groups.add(group)
        rule = RuleSet.objects.get(group=group, name='purchase_order')
        rule.can_change = True
        rule.save()
        part = Part.objects.create(name='Fictional archive part')
        supplier = Company.objects.create(
            name='Fictional archive supplier', is_supplier=True
        )
        supplier_part = SupplierPart.objects.create(
            part=part, supplier=supplier, SKU='FICTIONAL-ARCHIVE'
        )
        self.order = PurchaseOrder.objects.create(
            supplier=supplier, reference='FICTIONAL-AI-001'
        )
        line = PurchaseOrderLineItem.objects.create(
            order=self.order, part=supplier_part, quantity=1
        )
        location = StockLocation.objects.create(name='Fictional archive location')
        self.receipt = PurchaseReceipt.objects.create(
            idempotency_key=uuid.uuid4(),
            request_hash='a' * 64,
            purchase_order_line=line,
            location=location,
            quantity=1,
            received_by=self.user,
        )
        image = BytesIO()
        Image.new('RGB', (2, 2), 'white').save(image, format='PNG')
        self.attachment = Attachment(
            model_type='purchaseorder',
            model_id=self.order.pk,
            attachment=SimpleUploadedFile(
                'fictional-receipt.png', image.getvalue(), content_type='image/png'
            ),
            upload_user=self.user,
        )
        self.attachment.save(rebuild=False)
        self.binding = PartnerBinding.objects.create(
            deployment_id=DEPLOYMENT,
            user=self.user,
            enabled=True,
            write_enabled=True,
            is_default=True,
        )
        self.grant = AssistantGrant.objects.create(
            binding=self.binding,
            subject=self.user,
            object_type='purchase_receipt',
            object_ids=[str(self.receipt.pk)],
            actions=['receipt.read', 'receipt.link_archive'],
            continuous=True,
            authorization_reference='fictional-continuous-instruction',
            limits={'attachment_ids': [self.attachment.pk]},
        )

    def link(self, **overrides):
        """Reuse one durable command unless the test overrides the requested action."""
        values = {
            'binding_id': self.binding.pk,
            'grant_id': self.grant.pk,
            'grant_version': 1,
            'key': 'fictional-photo-command',
            'object_id': str(self.receipt.pk),
            'run_id': 'fictional-run',
            'step_id': 'link-photo',
            'arguments': {'attachment_id': self.attachment.pk, 'kind': 'photo'},
            'tool': LINK_ARCHIVE,
        }
        values.update(overrides)
        return execute_command(**values)

    def query(self):
        """Read live completeness through the same bounded subject and receipt."""
        return receipt_status(
            binding_id=self.binding.pk,
            grant_id=self.grant.pk,
            grant_version=1,
            receipt_id=self.receipt.pk,
        )


@override_settings(USE_TZ=True)
class ReceiptAssistantToolTests(ReceiptToolFixture, TestCase):
    """Exercise actual archive associations and their database effects."""

    def setUp(self):
        """Build one isolated fictional receipt."""
        self.build_fixture()

    def test_link_and_lost_response_retry_preserve_source_and_file(self):
        """Receipt association creates no second file and retries return one receipt."""
        original_name = self.attachment.attachment.name
        first = self.link()
        self.assertEqual(first.pk, self.link(run_id='recovered-run').pk)
        self.attachment.refresh_from_db()
        self.assertEqual(self.attachment.model_type, 'purchaseorder')
        self.assertEqual(self.attachment.model_id, self.order.pk)
        self.assertEqual(self.attachment.attachment.name, original_name)
        self.assertEqual(Attachment.objects.count(), 1)
        self.assertEqual(ReceiptArchiveEvidence.objects.count(), 1)
        self.assertEqual(AssistantCommand.objects.count(), 1)
        self.assertNotIn('photo', self.query()['missing'])
        self.assertFalse(self.query()['archive_ready'])
        self.assertIn('inspection', self.query()['missing'])
        self.assertIn('report', self.query()['missing'])

    def test_changed_command_and_out_of_scope_attachment_rejected(self):
        """Different intents and unregistered attachment IDs cannot reuse authority."""
        self.link()
        with self.assertRaises(CommandConflictError):
            self.link(arguments={'attachment_id': self.attachment.pk, 'kind': 'report'})
        from django.core.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            self.link(
                key='other-photo',
                arguments={'attachment_id': self.attachment.pk + 1, 'kind': 'photo'},
            )

    def test_cross_order_source_and_external_links_are_rejected(self):
        """Even allowed attachment IDs must satisfy real business/file preconditions."""
        from django.core.exceptions import ValidationError

        Attachment.objects.filter(pk=self.attachment.pk).update(
            model_id=self.order.pk + 1
        )
        with self.assertRaises(ValidationError):
            self.link()
        self.assertFalse(ReceiptArchiveEvidence.objects.exists())
        Attachment.objects.filter(pk=self.attachment.pk).update(
            model_id=self.order.pk,
            attachment='',
            link='https://example.invalid/fictional-photo',
        )
        with self.assertRaises(ValidationError):
            self.link()

    def test_changed_file_invalidates_archive_evidence(self):
        """An attachment ID cannot keep qualifying after its stored file changes."""
        self.link()
        with self.attachment.attachment.storage.open(
            self.attachment.attachment.name, 'wb'
        ) as handle:
            handle.write(b'fictional replaced content')
        self.assertIn('photo', self.query()['missing'])
        self.assertEqual(self.query()['evidence'], [])

    def test_inspection_and_signatures_are_never_supplied_by_the_tool(self):
        """File association is independent of actual human inspection responsibility."""
        self.link()
        self.assertFalse(PurchaseReceiptInspection.objects.exists())
        inspection = PurchaseReceiptInspection.objects.create(
            receipt=self.receipt, state='pass'
        )
        result = self.query()
        self.assertIn('inspector', result['missing'])
        self.assertIn('warehouse_signature', result['missing'])
        self.assertIn('purchaser_signature', result['missing'])
        inspection.refresh_from_db()
        self.assertIsNone(inspection.inspector_id)

    def test_receipt_and_native_attachment_events_share_rollback(self):
        """Ordinary ORM saves enqueue references in the business transaction."""
        before = AssistantOutboxEvent.objects.count()
        with self.assertRaises(RuntimeError), transaction.atomic():
            self.receipt.note = 'Fictional rolled-back update'
            self.receipt.save()
            raise RuntimeError('rollback')
        self.receipt.refresh_from_db()
        self.assertEqual(self.receipt.note, '')
        self.assertEqual(AssistantOutboxEvent.objects.count(), before)
        with patch(
            'cangxu.assistant_events.emit_receipt_change',
            side_effect=RuntimeError('outbox failed'),
        ):
            self.attachment.comment = 'Not committed'
            with self.assertRaises(RuntimeError):
                self.attachment.save(rebuild=False)
        self.attachment.refresh_from_db()
        self.assertEqual(self.attachment.comment, '')

    def test_service_identity_and_current_owner_scope(self):
        """Neither anonymous callers nor a token with another partner may execute."""
        factory = APIRequestFactory()
        payload = {
            'partner_id': str(self.binding.partner_id),
            'grant_id': self.grant.pk,
            'grant_version': 1,
            'tool': 'receipt_status',
            'object_id': str(self.receipt.pk),
        }
        env = {
            'ASSISTANT_RUNTIME_TOKEN': SERVICE_TOKEN,
            'ASSISTANT_DEPLOYMENT_ID': DEPLOYMENT,
        }
        with patch.dict(os.environ, env):
            response = AssistantInternalToolsView.as_view()(
                factory.post('/', payload, format='json')
            )
            self.assertEqual(response.status_code, 401)
            headers = {
                'HTTP_AUTHORIZATION': f'Bearer {SERVICE_TOKEN}',
                'HTTP_X_ASSISTANT_DEPLOYMENT': DEPLOYMENT,
            }
            response = AssistantInternalToolsView.as_view()(
                factory.post('/', payload, format='json', **headers)
            )
            self.assertEqual(response.status_code, 200)
            self.grant.revoked_at = timezone.now()
            self.grant.save()
            response = AssistantInternalToolsView.as_view()(
                factory.post('/', payload, format='json', **headers)
            )
            self.assertEqual(response.status_code, 403)
