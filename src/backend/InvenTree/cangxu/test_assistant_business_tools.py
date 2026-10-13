"""Existing business APIs as model tools: real queries, writes and role enforcement."""

import json
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings
from django.urls import resolve

from stock.models import StockItem
from users.models import RuleSet

from .assistant_business_tools import (
    ACTIONS,
    RESOURCES,
    business_action,
    business_capabilities,
    business_query,
)
from .assistant_knowledge import CATALOG, workflow_knowledge
from .assistant_models import AssistantCommand, AssistantGrant
from .assistant_services import CommandConflictError
from .models import CountSession
from .test_assistant_tools import ReceiptToolFixture


@override_settings(USE_TZ=True)
class ModelBusinessToolTests(ReceiptToolFixture, TestCase):
    """Tool calls have no additional grant prerequisite and reuse current app rights."""

    def setUp(self):
        """Build fictional records and give the normal user the existing stock role."""
        self.build_fixture()
        rule = RuleSet.objects.get(group=self.user.groups.first(), name='stock')
        rule.can_add = True
        rule.save()
        for name in ['part', 'bom', 'stock_location', 'build', 'sales_order']:
            read_role = RuleSet.objects.get(group=self.user.groups.first(), name=name)
            read_role.can_view = True
            read_role.save()
        # Prove that ad-hoc model tools do not require an extra authorization record.
        AssistantGrant.objects.all().delete()

    def action(self, operation='prepare_count', data=None, **overrides):
        """Send the runtime's stable command intent without a grant parameter."""
        payload = {
            'arguments': {
                'operation': operation,
                'data': data
                or {
                    'reference': 'FICTIONAL-MODEL-COUNT',
                    'location': self.receipt.location_id,
                },
            },
            'command_id': 'model:fictional-one',
            'run_id': 'tool-task-1',
            'step_id': 'call-1',
        }
        payload.update(overrides)
        return business_action(self.binding, payload)

    def test_query_and_action_routes_all_resolve_to_existing_apis(self):
        """The advertised inventory domains point at current APIs, not invented paths."""
        for name, path in RESOURCES.items():
            with self.subTest(resource=name):
                resolve(path)
                result = business_query(self.binding, {'resource': name, 'limit': 2})
                self.assertEqual(result['status'], 'ok')
        for name, action in ACTIONS.items():
            if action.path:
                with self.subTest(operation=name):
                    resolve(action.path.format(id=1))

    def test_actual_query_and_mutation_complete_without_grant_configuration(self):
        """Read a location, prepare an actual count and read its persisted business record."""
        query = business_query(
            self.binding, {'resource': 'locations', 'id': self.receipt.location_id}
        )
        self.assertEqual(query['data']['pk'], self.receipt.location_id)
        result = self.action()
        self.assertEqual(result['status'], 'succeeded')
        session = CountSession.objects.get(reference='FICTIONAL-MODEL-COUNT')
        self.assertEqual(session.started_by_id, self.user.pk)
        verify = business_query(
            self.binding, {'resource': 'count_sessions', 'id': session.pk}
        )
        self.assertEqual(verify['data']['reference'], session.reference)
        self.assertEqual(AssistantGrant.objects.count(), 0)

    def test_large_query_preserves_total_and_contiguous_next_page(self):
        """Rich native rows fit the bridge without silently skipping stock items."""
        rows = [{'pk': i, 'quantity': '2', 'notes': '虚构' * 1000} for i in range(100)]
        with patch(
            'cangxu.assistant_business_tools._original_api',
            return_value={
                'count': 555,
                'results': rows,
                'next': '/api/stock/?limit=100&offset=100',
            },
        ):
            result = business_query(self.binding, {'resource': 'stock', 'limit': 100})
        self.assertEqual(result['data']['count'], 555)
        self.assertTrue(result['page_limited'])
        self.assertGreater(len(result['data']['results']), 0)
        self.assertLess(len(json.dumps(result, ensure_ascii=False).encode()), 32768)
        self.assertEqual(result['next_offset'], len(result['data']['results']))
        self.assertIn(f'offset={result["next_offset"]}', result['data']['next'])
        self.assertEqual(
            [row['pk'] for row in result['data']['results']],
            list(range(result['next_offset'])),
        )

    def test_lost_response_replay_and_changed_intent(self):
        """The same durable tool intent returns one receipt and one domain effect."""
        first = self.action()
        again = self.action(run_id='recovered-task')
        self.assertEqual(first['command_receipt_id'], again['command_receipt_id'])
        self.assertTrue(again['replayed'])
        self.assertEqual(CountSession.objects.count(), 1)
        self.assertEqual(AssistantCommand.objects.count(), 1)
        with self.assertRaises(CommandConflictError):
            self.action(
                data={
                    'reference': 'DIFFERENT-COUNT',
                    'location': self.receipt.location_id,
                }
            )

    def test_current_business_permission_is_enforced_on_new_action_and_replay(self):
        """A prior success does not keep a removed stock role alive."""
        self.action()
        self.user.groups.clear()
        with self.assertRaises(PermissionDenied):
            self.action(command_id='new-without-rights')
        with self.assertRaises(PermissionDenied):
            self.action()
        self.assertEqual(CountSession.objects.count(), 1)

    def test_invalid_domain_data_rolls_back_receipt_and_domain_effect(self):
        """The original serializer's rejection cannot become a successful tool result."""
        with self.assertRaises(ValidationError):
            self.action(data={'reference': 'INVALID-COUNT', 'location': 999999})
        self.assertFalse(CountSession.objects.exists())
        self.assertFalse(AssistantCommand.objects.exists())
        with self.assertRaises(ValidationError):
            self.action(
                data={
                    'reference': 'INVALID-COUNT',
                    'location': self.receipt.location_id,
                    'state': 'closed',
                }
            )

    def test_exact_sn_query_preserves_cross_part_ambiguity(self):
        """The tool returns actual matching records rather than selecting a guessed part."""
        from part.models import Part

        for name in ['Fictional serial part A', 'Fictional serial part B']:
            part = Part.objects.create(name=name, trackable=True)
            StockItem.objects.create(
                part=part,
                serial='FICTIONAL-SAME-SN',
                quantity=1,
                location=self.receipt.location,
            )
        result = business_query(
            self.binding,
            {'resource': 'stock', 'filters': {'serial': 'FICTIONAL-SAME-SN'}},
        )
        data = result['data']
        records = data['results'] if isinstance(data, dict) else data
        self.assertEqual(len(records), 2)
        self.assertEqual(len({record['part'] for record in records}), 2)
        with self.assertRaises(ValidationError):
            business_query(
                self.binding,
                {
                    'resource': 'stock',
                    'filters': {'arbitrary_model_filter': 'anything'},
                },
            )

    def test_human_inspection_signature_and_approval_operations_are_not_exposed(self):
        """The model cannot select an approval URL or add inspection results to a movement."""
        for name in [
            'approve_receipt',
            'sign_receipt',
            'inspect_receipt',
            'close_count',
        ]:
            with self.assertRaises(ValidationError):
                self.action(operation=name)
        with self.assertRaises(ValidationError):
            self.action(
                operation='record_repair_movement',
                data={'line': 1, 'event_type': 'inspected'},
            )
        capabilities = business_capabilities(self.binding)
        self.assertEqual(len(capabilities['queries']), len(RESOURCES))
        self.assertEqual(len(capabilities['operations']), 13)
        self.assertNotIn('inspection_passed', str(capabilities['operations']))

    def test_workflow_knowledge_labels_sources_and_formal_material_gaps(self):
        """All domains have guidance while missing formal SOP stays explicit."""
        for code, *_ in CATALOG:
            result = workflow_knowledge({'query': '流程', 'process_id': code})
            self.assertEqual(len(result['items']), 1)
            self.assertFalse(result['items'][0]['formal_sop'])
            self.assertTrue(result['items'][0]['sources'])
            self.assertTrue(result['items'][0]['gap'])
        self.assertTrue(
            workflow_knowledge({'query': 'fictional unknown process'})['unknown']
        )

    def test_real_purchase_receipt_posts_native_stock_once(self):
        """Model receive uses the original PO transaction, never a second stock ledger."""
        from .models import PurchaseReceipt, PurchaseReceiptInspection

        rule = RuleSet.objects.get(
            group=self.user.groups.first(), name='purchase_order'
        )
        rule.can_add = True
        rule.save()
        self.order.place_order()
        data = {
            'purchase_order_line': self.receipt.purchase_order_line_id,
            'quantity': '1',
            'location': self.receipt.location_id,
        }
        first = self.action(operation='receive_purchase', data=data)
        again = self.action(operation='receive_purchase', data=data)
        self.assertEqual(first['command_receipt_id'], again['command_receipt_id'])
        posted = PurchaseReceipt.objects.exclude(pk=self.receipt.pk).get()
        self.assertEqual(posted.stock_items.count(), 1)
        self.assertEqual(posted.stock_items.first().quantity, 1)
        self.receipt.purchase_order_line.refresh_from_db()
        self.assertEqual(self.receipt.purchase_order_line.received, 1)
        self.assertFalse(PurchaseReceiptInspection.objects.exists())

    def test_linked_archive_is_retrievable_through_the_existing_receipt_api(self):
        """The actual user can query the new association without a separate grant."""
        result = self.action(
            operation='link_receipt_archive',
            data={
                'receipt_id': self.receipt.pk,
                'attachment_id': self.attachment.pk,
                'kind': 'photo',
            },
        )
        self.assertEqual(result['status'], 'succeeded')
        query = business_query(
            self.binding, {'resource': 'purchase_receipts', 'id': self.receipt.pk}
        )
        evidence = query['data']['archive_evidence']
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]['attachment_id'], self.attachment.pk)
        self.assertEqual(evidence[0]['kind'], 'photo')
        self.assertEqual(AssistantGrant.objects.count(), 0)

    def _chat_upload(self):
        """Persist a fictional private image in isolated chat storage."""
        from io import BytesIO
        from unittest.mock import patch

        from django.core.files.uploadedfile import SimpleUploadedFile

        from PIL import Image

        from .assistant_attachment_models import (
            AssistantChatAttachment,
            PrivateChatStorage,
        )
        from .assistant_attachments import create_upload

        storage = patch.object(
            AssistantChatAttachment._meta.get_field('file'),
            'storage',
            PrivateChatStorage(location=self.files.name + '/private'),
        )
        storage.start()
        self.addCleanup(storage.stop)
        content = BytesIO()
        Image.new('RGB', (2, 3), 'blue').save(content, format='PNG')
        upload, _ = create_upload(
            self.binding,
            SimpleUploadedFile(
                'fictional-chat-photo.png', content.getvalue(), content_type='image/png'
            ),
            'fictional-chat-upload',
        )
        return upload

    def test_chat_upload_promotes_to_native_attachment_then_archive_query(self):
        """A private upload becomes genuine native evidence through explicit business actions."""
        from common.models import Attachment

        chat = self._chat_upload()
        data = {
            'chat_attachment_id': str(chat.pk),
            'object_type': 'purchase_receipt',
            'object_id': self.receipt.pk,
            'comment': 'Fictional receipt photo',
        }
        before = Attachment.objects.count()
        promoted = self.action(
            operation='attach_chat_file', data=data, command_id='promote-chat'
        )
        replay = self.action(
            operation='attach_chat_file',
            data=data,
            command_id='promote-chat',
            run_id='recovered',
        )
        self.assertTrue(replay['replayed'])
        self.assertEqual(promoted['command_receipt_id'], replay['command_receipt_id'])
        self.assertEqual(Attachment.objects.count(), before + 1)
        native_id = promoted['data']['attachment_id']
        native = Attachment.objects.get(pk=native_id)
        self.assertEqual(
            (native.model_type, native.model_id, native.upload_user_id),
            ('purchasereceipt', self.receipt.pk, self.user.pk),
        )
        self.assertEqual(native.attachment.read(), chat.file.read())
        self.assertTrue(chat.file.storage.exists(chat.file.name))
        self.action(
            operation='link_receipt_archive',
            data={
                'receipt_id': self.receipt.pk,
                'attachment_id': native_id,
                'kind': 'photo',
            },
            command_id='archive-chat',
        )
        queried = business_query(
            self.binding, {'resource': 'purchase_receipts', 'id': self.receipt.pk}
        )
        self.assertEqual(
            queried['data']['archive_evidence'][0]['attachment_id'], native_id
        )
        chat.refresh_from_db()
        self.assertIsNotNone(chat.submitted_at)

    def test_chat_promotion_enforces_owner_and_current_native_permission(self):
        """Possession of a chat UUID never confers native business change permission."""
        import uuid

        chat = self._chat_upload()
        data = {
            'chat_attachment_id': str(uuid.uuid4()),
            'object_type': 'purchase_order',
            'object_id': self.order.pk,
        }
        with self.assertRaises(ValidationError):
            self.action(operation='attach_chat_file', data=data)
        data['chat_attachment_id'] = str(chat.pk)
        self.action(operation='attach_chat_file', data=data)
        role = RuleSet.objects.get(
            group=self.user.groups.first(), name='purchase_order'
        )
        role.can_change = False
        role.save()
        with self.assertRaises(PermissionDenied):
            self.action(operation='attach_chat_file', data=data)

    def test_chat_promotion_failed_receipt_rolls_back_native_copy(self):
        """A command-record failure removes its native file copy and database association."""
        from unittest.mock import patch

        from common.models import Attachment

        chat = self._chat_upload()
        before = Attachment.objects.count()
        with patch(
            'cangxu.assistant_business_tools.AssistantCommand.objects.create',
            side_effect=RuntimeError('fictional failed receipt'),
        ):
            with self.assertRaises(RuntimeError):
                self.action(
                    operation='attach_chat_file',
                    data={
                        'chat_attachment_id': str(chat.pk),
                        'object_type': 'purchase_order',
                        'object_id': self.order.pk,
                    },
                )
        self.assertEqual(Attachment.objects.count(), before)
        self.assertTrue(chat.file.storage.exists(chat.file.name))
        chat.refresh_from_db()
        self.assertIsNone(chat.submitted_at)
