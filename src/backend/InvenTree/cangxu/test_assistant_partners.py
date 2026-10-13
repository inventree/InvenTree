"""Multi-partner workbench: sidebar list, selectors, isolation and defaults."""

import os
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase, override_settings

from rest_framework.test import APIRequestFactory, force_authenticate

from .assistant_api import (
    AssistantControlViewSet,
    AssistantMessageViewSet,
    AssistantPartnerViewSet,
    AssistantStatusViewSet,
)
from .assistant_attachment_api import AssistantAttachmentViewSet
from .assistant_attachment_models import AssistantChatAttachment
from .assistant_attachments import create_upload
from .assistant_delivery_models import AssistantGatewayDelivery
from .assistant_gateway import ensure_partner_binding
from .assistant_models import PartnerBinding
from .test_assistant_tools import DEPLOYMENT, SERVICE_TOKEN

ENV = {
    'ASSISTANT_DEPLOYMENT_ID': DEPLOYMENT,
    'ASSISTANT_RUNTIME_TOKEN': SERVICE_TOKEN,
    'ASSISTANT_RUNTIME_URL': 'http://127.0.0.1:8789',
}


@override_settings(USE_TZ=True)
class AssistantPartnerTests(TestCase):
    """Use fictional users and partners only; no real enterprise data."""

    def setUp(self):
        """Configure a fictional deployment and two isolated owners."""
        self.env = patch.dict(os.environ, ENV)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.user = get_user_model().objects.create_user(
            username='fictional-workbench-owner'
        )
        self.other = get_user_model().objects.create_user(
            username='fictional-workbench-stranger'
        )
        self.factory = APIRequestFactory()

    def partners(self, method, data=None, user=None, pk=None):
        """Invoke the partners endpoint as the selected fictional owner."""
        action = (
            {'get': 'list', 'post': 'create'}[method]
            if pk is None
            else {'patch': 'partial_update'}[method]
        )
        request = getattr(self.factory, method)('/', data or {}, format='json')
        force_authenticate(request, user=user or self.user)
        view = AssistantPartnerViewSet.as_view({method: action})
        return view(request) if pk is None else view(request, pk=pk)

    def selected(self, view, action, partner_id, data=None, method='post', user=None):
        """Invoke one assistant endpoint with an explicit partner selector."""
        fmt = 'multipart' if 'file' in (data or {}) else 'json'
        request = getattr(self.factory, method)(
            f'/?partner_id={partner_id}', data or {}, format=fmt
        )
        force_authenticate(request, user=user or self.user)
        return view.as_view({method: action})(request)

    def create_second(self, name='第二工作伙伴'):
        """Create the caller's second partner through the real endpoint."""
        response = self.partners('post', {'display_name': name})
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def test_list_provisions_default_once_and_orders_default_first(self):
        """Opening the workbench creates exactly one enabled default partner."""
        first = self.partners('get')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(len(first.data['results']), 1)
        default = first.data['results'][0]
        self.assertTrue(default['is_default'])
        self.assertTrue(default['enabled'])
        self.assertTrue(default['write_enabled'])
        self.assertEqual(default['display_name'], '工作伙伴')
        self.assertIsNone(default['last_message'])
        self.partners('get')
        self.assertEqual(PartnerBinding.objects.count(), 1)
        second = self.create_second()
        listed = self.partners('get').data['results']
        self.assertEqual(
            str(listed[0]['partner_id']),
            str(PartnerBinding.objects.get(is_default=True).partner_id),
        )
        self.assertIn(
            str(second['partner_id']), [str(row['partner_id']) for row in listed]
        )
        self.assertEqual(
            set(listed[0]),
            {
                'partner_id',
                'conversation_id',
                'display_name',
                'is_default',
                'enabled',
                'write_enabled',
                'created_at',
                'updated_at',
                'last_message',
                'last_message_at',
            },
        )

    def test_first_open_validation_race_reuses_the_existing_default(self):
        """A full_clean uniqueness race does not break a second browser opening."""
        from django.core.exceptions import ValidationError

        from .assistant_gateway import ensure_partner_binding

        expected = ensure_partner_binding(self.user)
        with patch.object(
            PartnerBinding.objects,
            'get_or_create',
            side_effect=ValidationError('Synthetic concurrent insert'),
        ):
            self.assertEqual(ensure_partner_binding(self.user).pk, expected.pk)
        self.assertEqual(
            PartnerBinding.objects.filter(user=self.user, is_default=True).count(), 1
        )

    def test_create_uses_server_owned_identity_and_rename_is_owner_only(self):
        """Client-supplied identity fields are rejected; renames stay isolated."""
        response = self.partners(
            'post', {'display_name': '虚构伙伴', 'partner_id': str(uuid.uuid4())}
        )
        self.assertEqual(response.status_code, 400)
        created = self.create_second('虚构伙伴')
        binding = PartnerBinding.objects.get(partner_id=created['partner_id'])
        self.assertTrue(binding.enabled and binding.write_enabled)
        self.assertFalse(binding.is_default)
        renamed = self.partners(
            'patch', {'display_name': '改名伙伴'}, pk=created['partner_id']
        )
        self.assertEqual(renamed.status_code, 200)
        self.assertEqual(renamed.data['display_name'], '改名伙伴')
        self.assertEqual(
            self.partners(
                'patch',
                {'display_name': '越权'},
                pk=created['partner_id'],
                user=self.other,
            ).status_code,
            404,
        )
        self.assertEqual(
            self.partners(
                'patch', {'display_name': ''}, pk=created['partner_id']
            ).status_code,
            400,
        )
        # Sidebar lists never expose another user's partners.
        other_rows = self.partners('get', user=self.other).data['results']
        self.assertEqual(len(other_rows), 1)
        self.assertTrue(all(row['is_default'] for row in other_rows))
        self.assertNotIn(
            str(created['partner_id']), [str(row['partner_id']) for row in other_rows]
        )

    @patch('cangxu.assistant_api._offload_delivery')
    def test_selected_partners_keep_separate_messages_status_and_last_message(
        self, offload
    ):
        """Two partners of one user hold independent queues and previews."""
        self.partners('get')
        default = PartnerBinding.objects.get(user=self.user, is_default=True)
        second = self.create_second()
        payload = {'client_request_id': 'second-only', 'text': '只在第二个伙伴里说'}
        response = self.selected(
            AssistantMessageViewSet, 'create', second['partner_id'], payload
        )
        self.assertEqual(response.status_code, 201, response.data)
        delivery = AssistantGatewayDelivery.objects.get()
        self.assertEqual(str(delivery.binding.partner_id), str(second['partner_id']))
        listed = self.partners('get').data['results']
        preview = {str(row['partner_id']): row for row in listed}[
            str(second['partner_id'])
        ]
        self.assertEqual(preview['last_message'], '只在第二个伙伴里说')
        self.assertIsNotNone(preview['last_message_at'])
        default_row = {str(row['partner_id']): row for row in listed}[
            str(default.partner_id)
        ]
        self.assertIsNone(default_row['last_message'])
        # Without a selector the default partner keeps the old behavior.
        response = self.api_message({'client_request_id': 'legacy', 'text': '默认'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            AssistantGatewayDelivery.objects.get(
                request_key='legacy'
            ).binding.partner_id,
            default.partner_id,
        )
        with patch('cangxu.assistant_api.get_runtime_transport') as transport:
            transport.return_value.partner_status.return_value = {
                'status': 'idle',
                'is_running': False,
            }
            response = self.selected(
                AssistantStatusViewSet, 'list', second['partner_id'], method='get'
            )
            self.assertEqual(response.status_code, 200)
            transport.return_value.partner_status.assert_called_once_with(
                second['partner_id']
            )

    def api_message(self, payload):
        """Send one selector-less message through the real endpoint."""
        request = self.factory.post('/', payload, format='json')
        force_authenticate(request, user=self.user)
        return AssistantMessageViewSet.as_view({'post': 'create'})(request)

    @patch('cangxu.assistant_api._offload_delivery')
    def test_foreign_and_unknown_selectors_are_rejected_everywhere(self, offload):
        """A caller-chosen identifier never provisions or reaches foreign state."""
        self.partners('get')
        foreign = ensure_partner_binding(self.other)
        unknown = uuid.uuid4()
        before = PartnerBinding.objects.count()
        for selector in [foreign.partner_id, unknown]:
            message = self.selected(
                AssistantMessageViewSet,
                'create',
                selector,
                {'client_request_id': f'm-{selector}', 'text': 'x'},
            )
            self.assertEqual(message.status_code, 404)
            history = self.selected(
                AssistantMessageViewSet, 'list', selector, method='get'
            )
            self.assertEqual(history.status_code, 404)
            control = self.selected(
                AssistantControlViewSet,
                'create',
                selector,
                {'client_request_id': f'c-{selector}', 'scope': 'reply'},
            )
            self.assertEqual(control.status_code, 404)
            status_response = self.selected(
                AssistantStatusViewSet, 'list', selector, method='get'
            )
            self.assertEqual(status_response.status_code, 404)
            upload = self.selected(
                AssistantAttachmentViewSet,
                'create',
                selector,
                {'client_upload_id': f'u-{selector}', 'file': self.file()},
                method='post',
            )
            self.assertEqual(upload.status_code, 404)
        self.assertEqual(PartnerBinding.objects.count(), before)
        self.assertFalse(AssistantGatewayDelivery.objects.exists())
        self.assertFalse(AssistantChatAttachment.objects.exists())
        for malformed_id in ('not-a-uuid', ''):
            malformed = self.selected(
                AssistantMessageViewSet, 'list', malformed_id, method='get'
            )
            self.assertEqual(malformed.status_code, 400)

    def file(self, name='fictional.txt', data=b'fictional bytes'):
        """Build one synthetic upload file."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        return SimpleUploadedFile(name, data)

    def test_selected_uploads_and_cross_partner_send_isolation(self):
        """Files belong to the selected partner and cannot cross into another."""
        import tempfile

        from .assistant_attachment_models import PrivateChatStorage

        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        storage = patch.object(
            AssistantChatAttachment._meta.get_field('file'),
            'storage',
            PrivateChatStorage(location=directory.name),
        )
        storage.start()
        self.addCleanup(storage.stop)
        self.partners('get')
        default = PartnerBinding.objects.get(user=self.user, is_default=True)
        second = self.create_second()
        upload = self.selected(
            AssistantAttachmentViewSet,
            'create',
            second['partner_id'],
            {'client_upload_id': 'second-file', 'file': self.file()},
        )
        self.assertEqual(upload.status_code, 201, upload.data)
        self.assertIn(
            f'?partner_id={second["partner_id"]}', upload.data['download_url']
        )
        item = AssistantChatAttachment.objects.get()
        self.assertEqual(str(item.binding.partner_id), str(second['partner_id']))
        # The metadata URL resolves against the selected binding.
        request = self.factory.get(upload.data['download_url'])
        force_authenticate(request, user=self.user)
        download = AssistantAttachmentViewSet.as_view({'get': 'download'})(
            request, pk=item.pk
        )
        self.assertEqual(download.status_code, 200)
        # Selector-less access still serves the default partner's own files.
        legacy, _ = create_upload(default, self.file(name='legacy.txt'), 'legacy')
        request = self.factory.get('/')
        force_authenticate(request, user=self.user)
        self.assertEqual(
            AssistantAttachmentViewSet.as_view({'get': 'retrieve'})(
                request, pk=legacy.pk
            ).status_code,
            200,
        )
        # A file uploaded to the default partner cannot be sent to the second.
        with patch('cangxu.assistant_api._offload_delivery'):
            rejected = self.selected(
                AssistantMessageViewSet,
                'create',
                second['partner_id'],
                {
                    'client_request_id': 'cross-send',
                    'text': '',
                    'attachments': [str(legacy.pk)],
                },
            )
        self.assertEqual(rejected.status_code, 400)
        self.assertFalse(
            AssistantGatewayDelivery.objects.filter(request_key='cross-send').exists()
        )


@override_settings(USE_TZ=True)
class AssistantPartnerMigrationTests(TransactionTestCase):
    """Replay 0023 -> 0024 on the test database with synthetic rows."""

    migrate_from = ('cangxu', '0023_assistantchatattachment_submitted_at')
    migrate_to = ('cangxu', '0024_partner_workbench')

    def test_existing_rows_become_default_and_keep_identity(self):
        """Existing partner/conversation identifiers and flags survive 0024."""
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])
        try:
            old_apps = executor.loader.project_state([self.migrate_from]).apps
            old_binding = old_apps.get_model('cangxu', 'PartnerBinding')
            user = get_user_model().objects.create_user(
                username='fictional-migration-owner'
            )
            row = old_binding.objects.create(
                deployment_id=DEPLOYMENT,
                user_id=user.pk,
                enabled=True,
                write_enabled=True,
            )
            partner_id, conversation_id = row.partner_id, row.conversation_id
            executor.loader.build_graph()
            executor.migrate([self.migrate_to])
            binding = PartnerBinding.objects.get(pk=row.pk)
            self.assertTrue(binding.is_default)
            self.assertEqual(binding.display_name, '工作伙伴')
            self.assertEqual(binding.partner_id, partner_id)
            self.assertEqual(binding.conversation_id, conversation_id)
            self.assertTrue(binding.enabled and binding.write_enabled)
        finally:
            executor.loader.build_graph()
            executor.migrate([executor.loader.graph.leaf_nodes('cangxu')[0]])
