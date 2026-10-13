"""Synthetic private chat files: identity, retry, MIME and actual model input."""

import io
import os
import tempfile
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import OperationalError, connection, connections
from django.test import TestCase, TransactionTestCase

from PIL import Image
from rest_framework.test import APIRequestFactory, force_authenticate

from .assistant_api import AssistantMessageViewSet
from .assistant_attachment_api import (
    AssistantAttachmentViewSet,
    AssistantInternalAttachmentView,
)
from .assistant_attachment_models import AssistantChatAttachment
from .assistant_attachments import model_attachment_content
from .assistant_gateway import ensure_partner_binding
from .test_assistant_tools import DEPLOYMENT, SERVICE_TOKEN


class AssistantAttachmentTests(TestCase):
    """Never use enterprise files or a real model for storage/auth tests."""

    def setUp(self):
        """Use a private isolated directory and fictional owners."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        from .assistant_attachment_models import PrivateChatStorage

        storage_patch = patch.object(
            AssistantChatAttachment._meta.get_field('file'),
            'storage',
            PrivateChatStorage(
                location=self.directory.name,
                file_permissions_mode=0o600,
                directory_permissions_mode=0o700,
            ),
        )
        storage_patch.start()
        self.addCleanup(storage_patch.stop)
        env = patch.dict(
            os.environ,
            {
                'ASSISTANT_DEPLOYMENT_ID': DEPLOYMENT,
                'ASSISTANT_RUNTIME_TOKEN': SERVICE_TOKEN,
                'ASSISTANT_RUNTIME_URL': 'http://127.0.0.1:8789',
                'ASSISTANT_ATTACHMENT_ROOT': self.directory.name,
            },
        )
        env.start()
        self.addCleanup(env.stop)
        self.user = get_user_model().objects.create_user(
            username='synthetic-chat-owner'
        )
        self.other = get_user_model().objects.create_user(
            username='synthetic-chat-other'
        )
        self.factory = APIRequestFactory()
        self.binding = ensure_partner_binding(self.user)
        ensure_partner_binding(self.other)

    def upload(
        self,
        data=b'fictional order alpha',
        name='sample.txt',
        key='upload-one',
        user=None,
    ):
        """Exercise the actual multipart view and authentication."""
        request = self.factory.post(
            '/api/cangxu/assistant/attachments/',
            {'client_upload_id': key, 'file': SimpleUploadedFile(name, data)},
            format='multipart',
        )
        force_authenticate(request, user=user or self.user)
        return AssistantAttachmentViewSet.as_view({'post': 'create'})(request)

    def test_upload_retry_conflict_and_private_storage(self):
        """Retry returns one upload; altered content under the same key conflicts."""
        first = self.upload()
        self.assertEqual(first.status_code, 201)
        self.assertEqual(self.upload().status_code, 200)
        self.assertEqual(self.upload(b'changed').status_code, 409)
        self.assertEqual(AssistantChatAttachment.objects.count(), 1)
        item = AssistantChatAttachment.objects.get()
        self.assertTrue(item.file.path.startswith(self.directory.name))
        with self.assertRaises(ValueError):
            _ = item.file.url
        self.assertIn('/api/cangxu/assistant/attachments/', first.data['download_url'])

    def test_download_and_metadata_are_owner_only(self):
        """Cross-user guessed UUIDs cannot read originals or metadata."""
        item_id = self.upload().data['id']
        for action in ['retrieve', 'download']:
            for owner, expected in [(self.user, 200), (self.other, 404)]:
                request = self.factory.get('/')
                force_authenticate(request, user=owner)
                response = AssistantAttachmentViewSet.as_view({'get': action})(
                    request, pk=item_id
                )
                self.assertEqual(response.status_code, expected)
                if response.status_code == 200 and action == 'download':
                    self.assertEqual(
                        b''.join(response.streaming_content), b'fictional order alpha'
                    )
                    self.assertEqual(response['Cache-Control'], 'private, no-store')
        request = self.factory.get('/')
        self.assertIn(
            AssistantAttachmentViewSet.as_view({'get': 'download'})(
                request, pk=item_id
            ).status_code,
            [401, 403],
        )

    def test_mime_spoof_empty_size_and_duplicate_attachment_rejected(self):
        """File bytes are validated and message references remain bounded."""
        self.assertEqual(self.upload(b'<svg>bad</svg>', 'pretend.png').status_code, 400)
        self.assertEqual(self.upload(b'', 'empty.txt').status_code, 400)
        with patch('cangxu.assistant_attachments.FILE_LIMIT', 3):
            self.assertEqual(self.upload(b'four', 'large.txt').status_code, 400)
        item_id = self.upload().data['id']
        for ids in [[item_id, item_id], [str(uuid.uuid4())]]:
            request = self.factory.post(
                '/',
                {
                    'client_request_id': str(uuid.uuid4()),
                    'text': '',
                    'attachments': ids,
                },
                format='json',
            )
            force_authenticate(request, user=self.user)
            self.assertEqual(
                AssistantMessageViewSet.as_view({'post': 'create'})(
                    request
                ).status_code,
                400,
            )

    @patch('cangxu.assistant_api._offload_delivery')
    def test_attachment_message_persistence_replay_and_pending_history(self, offload):
        """File-only input remains visible while transport is down and retries dedupe."""
        item_id = self.upload().data['id']
        payload = {
            'client_request_id': 'file-message',
            'text': '',
            'attachments': [item_id],
        }
        for expected in [201, 200]:
            request = self.factory.post('/', payload, format='json')
            force_authenticate(request, user=self.user)
            self.assertEqual(
                AssistantMessageViewSet.as_view({'post': 'create'})(
                    request
                ).status_code,
                expected,
            )
        request = self.factory.get('/')
        force_authenticate(request, user=self.user)
        with patch('cangxu.assistant_api.get_runtime_transport') as transport:
            from .assistant_gateway import RuntimeUnavailableError

            transport.return_value.list_messages.side_effect = RuntimeUnavailableError(
                'network'
            )
            result = AssistantMessageViewSet.as_view({'get': 'list'})(request)
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.data['runtime_unavailable'])
        self.assertEqual(result.data['pending'][0]['attachments'][0]['id'], item_id)

    def test_internal_model_content_identity_and_integrity(self):
        """Actual UTF-8 content is returned only to the matching service/partner."""
        item_id = self.upload('虚构附件内容'.encode()).data['id']
        url = f'/?partner_id={self.binding.partner_id}'
        view = AssistantInternalAttachmentView.as_view()
        self.assertEqual(
            view(self.factory.get(url), attachment_id=item_id).status_code, 401
        )
        headers = {
            'HTTP_AUTHORIZATION': f'Bearer {SERVICE_TOKEN}',
            'HTTP_X_ASSISTANT_DEPLOYMENT': DEPLOYMENT,
        }
        response = view(self.factory.get(url, **headers), attachment_id=item_id)
        self.assertEqual(response.status_code, 200)
        self.assertIn('虚构附件内容', response.data['content'][0]['text'])
        other = ensure_partner_binding(self.other)
        self.assertEqual(
            view(
                self.factory.get(f'/?partner_id={other.partner_id}', **headers),
                attachment_id=item_id,
            ).status_code,
            404,
        )
        item = AssistantChatAttachment.objects.get()
        with open(item.file.path, 'wb') as output:
            output.write(b'corrupt')
        self.assertEqual(
            view(self.factory.get(url, **headers), attachment_id=item_id).status_code,
            409,
        )

    def test_image_actual_model_content_and_document_extraction(self):
        """Vision input contains decoded image bytes; office data is extracted."""
        output = io.BytesIO()
        Image.new('RGB', (3, 2), 'blue').save(output, format='PNG')
        image = self.upload(output.getvalue(), 'fictional.png').data
        self.assertEqual((image['kind'], image['image_width']), ('image', 3))
        content = model_attachment_content(
            AssistantChatAttachment.objects.get(pk=image['id'])
        )
        self.assertEqual(content['content'][0]['type'], 'image')
        self.assertEqual(content['content'][0]['mimeType'], 'image/jpeg')
        import openpyxl

        book = openpyxl.Workbook()
        book.active.append(['fictional part', 3])
        output = io.BytesIO()
        book.save(output)
        document = self.upload(output.getvalue(), 'fictional.xlsx', key='sheet').data
        content = model_attachment_content(
            AssistantChatAttachment.objects.get(pk=document['id'])
        )
        self.assertIn('fictional part\t3', content['content'][0]['text'])

    @patch('cangxu.assistant_api._offload_delivery')
    def test_explicit_failed_retry_reuses_delivery_and_preserves_intent(self, offload):
        """An explicit retry requeues the existing command, never creates another."""
        from .assistant_delivery_models import AssistantGatewayDelivery

        payload = {'client_request_id': 'retry-message', 'text': 'fictional request'}
        request = self.factory.post('/', payload, format='json')
        force_authenticate(request, user=self.user)
        self.assertEqual(
            AssistantMessageViewSet.as_view({'post': 'create'})(request).status_code,
            201,
        )
        delivery = AssistantGatewayDelivery.objects.get(binding=self.binding)
        digest = delivery.request_hash
        delivery.status = 'failed'
        delivery.attempts = 8
        delivery.last_error = 'network_unreachable'
        delivery.save()
        request = self.factory.post('/', {**payload, 'retry': True}, format='json')
        force_authenticate(request, user=self.user)
        self.assertEqual(
            AssistantMessageViewSet.as_view({'post': 'create'})(request).status_code,
            200,
        )
        delivery.refresh_from_db()
        self.assertEqual(
            (delivery.status, delivery.attempts, delivery.request_hash),
            ('pending', 0, digest),
        )
        self.assertEqual(AssistantGatewayDelivery.objects.count(), 1)

    @patch('cangxu.assistant_api._offload_delivery')
    def test_remove_draft_but_preserve_submitted_attachment(self, offload):
        """Draft removal cleans storage; conversation-linked files cannot disappear."""
        first = self.upload().data['id']
        request = self.factory.delete('/')
        force_authenticate(request, user=self.user)
        with self.captureOnCommitCallbacks(execute=True):
            response = AssistantAttachmentViewSet.as_view({'delete': 'destroy'})(
                request, pk=first
            )
        self.assertEqual(response.status_code, 204)
        second = self.upload(key='second').data['id']
        request = self.factory.post(
            '/',
            {'client_request_id': 'with-file', 'attachments': [second]},
            format='json',
        )
        force_authenticate(request, user=self.user)
        self.assertEqual(
            AssistantMessageViewSet.as_view({'post': 'create'})(request).status_code,
            201,
        )
        request = self.factory.delete('/')
        force_authenticate(request, user=self.user)
        self.assertEqual(
            AssistantAttachmentViewSet.as_view({'delete': 'destroy'})(
                request, pk=second
            ).status_code,
            409,
        )

    def test_history_preserves_extraction_warning_with_trusted_urls(self):
        """Read warnings survive reload while untrusted runtime URLs are replaced."""
        file = self.upload().data
        request = self.factory.get('/')
        force_authenticate(request, user=self.user)
        with patch('cangxu.assistant_api.get_runtime_transport') as transport:
            transport.return_value.list_messages.return_value = {
                'items': [
                    {
                        'id': 1,
                        'text': '',
                        'attachments': [
                            {
                                **file,
                                'preview_url': 'https://untrusted.invalid/',
                                'extraction_status': 'truncated',
                                'extraction_note': 'First rows only',
                            }
                        ],
                    }
                ],
                'next_before': None,
                'has_more': False,
            }
            response = AssistantMessageViewSet.as_view({'get': 'list'})(request)
        attachment = response.data['items'][0]['attachments'][0]
        self.assertEqual(attachment['extraction_status'], 'truncated')
        self.assertEqual(attachment['extraction_note'], 'First rows only')
        self.assertIsNone(attachment['preview_url'])

    def test_docx_text_and_scanned_pdf_limits_are_explicit(self):
        """Extract real Office text and identify PDFs without a readable text layer."""
        import zipfile

        from pypdf import PdfWriter

        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as package:
            package.writestr(
                'word/document.xml',
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>fictional document evidence</w:t></w:r></w:p></w:body></w:document>',
            )
        uploaded = self.upload(output.getvalue(), 'fictional.docx', key='docx')
        self.assertEqual(uploaded.status_code, 201)
        extracted = model_attachment_content(
            AssistantChatAttachment.objects.get(pk=uploaded.data['id'])
        )
        self.assertIn('fictional document evidence', extracted['content'][0]['text'])
        output = io.BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.write(output)
        uploaded = self.upload(output.getvalue(), 'blank.pdf', key='pdf')
        self.assertEqual(uploaded.status_code, 201)
        extracted = model_attachment_content(
            AssistantChatAttachment.objects.get(pk=uploaded.data['id'])
        )
        self.assertEqual(extracted['extraction_status'], 'unsupported')
        self.assertIn('no extractable text', extracted['extraction_note'])


class AssistantConcurrentUploadTests(TransactionTestCase):
    """Fresh connections exercise SQLite writer reservation and stable-key races."""

    def setUp(self):
        """Use isolated private files and actual committed user/binding rows."""
        from .assistant_attachment_models import PrivateChatStorage
        from .assistant_models import PartnerBinding

        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        storage = patch.object(
            AssistantChatAttachment._meta.get_field('file'),
            'storage',
            PrivateChatStorage(location=self.directory.name),
        )
        storage.start()
        self.addCleanup(storage.stop)
        self.user = get_user_model().objects.create_user(
            username='fictional-concurrent-uploader'
        )
        self.binding = PartnerBinding.objects.create(
            user=self.user, deployment_id=DEPLOYMENT, enabled=True, write_enabled=True
        )

    def test_simultaneous_uploads_with_duplicate_keys_do_not_lose_files(self):
        """Four real threads and separate DB connections create exactly two uploads."""
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier

        from .assistant_attachments import create_upload
        from .assistant_models import PartnerBinding

        barrier = Barrier(4)
        binding_id = self.binding.pk

        def upload(index):
            try:
                binding = PartnerBinding.objects.get(pk=binding_id)
                barrier.wait(timeout=10)
                result, created = create_upload(
                    binding,
                    SimpleUploadedFile(
                        f'fictional-{index % 2}.csv', b'part,qty\nfictional,2\n'
                    ),
                    f'parallel-{index % 2}',
                )
                return str(result.pk), created
            finally:
                connections['default'].close()

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(upload, range(4)))
        self.assertEqual(len({identifier for identifier, _ in results}), 2)
        self.assertEqual(sum(created for _, created in results), 2)
        self.assertEqual(AssistantChatAttachment.objects.count(), 2)
        from pathlib import Path

        self.assertEqual(
            sum(path.is_file() for path in Path(self.directory.name).rglob('*')), 2
        )
        for item in AssistantChatAttachment.objects.all():
            self.assertEqual(item.file.read(), b'part,qty\nfictional,2\n')

    def test_busy_retry_cap_and_nonbusy_database_errors(self):
        """Only SQLite contention retries; exhaustion returns a structured 503."""
        from .assistant_database import AssistantDatabaseBusy, sqlite_busy_retry

        if connection.vendor != 'sqlite':
            self.skipTest('SQLite-specific contention policy')
        with (
            patch('cangxu.assistant_database.time.sleep'),
            patch(
                'cangxu.assistant_attachments._persist_upload',
                side_effect=OperationalError('database is locked'),
            ) as persist,
        ):
            from .assistant_attachments import create_upload

            with self.assertRaises(AssistantDatabaseBusy) as failure:
                create_upload(
                    self.binding,
                    SimpleUploadedFile('fictional.txt', b'content'),
                    'busy',
                )
            self.assertEqual(failure.exception.status_code, 503)
            self.assertEqual(persist.call_count, 5)
        operation = patch(
            'cangxu.assistant_attachments._persist_upload',
            side_effect=OperationalError('unrelated failure'),
        )
        with operation as persist:
            with self.assertRaises(OperationalError):
                sqlite_busy_retry(persist)
            self.assertEqual(persist.call_count, 1)
        self.assertEqual(AssistantChatAttachment.objects.count(), 0)

    def test_retry_removes_uncommitted_file_before_next_attempt(self):
        """Content saved before a transient DB failure does not leave an orphan copy."""
        from pathlib import Path

        from .assistant_attachments import create_upload

        if connection.vendor != 'sqlite':
            self.skipTest('SQLite-specific contention policy')
        original_save = AssistantChatAttachment.save
        attempts = []

        def fail_once(item, *args, **kwargs):
            attempts.append(str(item.pk))
            if len(attempts) == 1:
                raise OperationalError('database is locked')
            return original_save(item, *args, **kwargs)

        with (
            patch.object(AssistantChatAttachment, 'save', fail_once),
            patch('cangxu.assistant_database.time.sleep'),
        ):
            item, created = create_upload(
                self.binding,
                SimpleUploadedFile('fictional.txt', b'content'),
                'save-retry',
            )
        self.assertTrue(created)
        self.assertEqual(len(attempts), 2)
        self.assertEqual(AssistantChatAttachment.objects.count(), 1)
        self.assertEqual(
            sum(path.is_file() for path in Path(self.directory.name).rglob('*')), 1
        )
        self.assertEqual(item.file.read(), b'content')
