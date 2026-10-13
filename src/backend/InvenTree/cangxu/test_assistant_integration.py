"""No-browser Pi HTTP to Django integration against real fictional business records."""

import json
import os
import select
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from unittest import skipUnless
from unittest.mock import patch

from django.test import LiveServerTestCase, override_settings
from django.urls import include, path

from .assistant_business_models import ReceiptArchiveEvidence
from .assistant_models import AssistantCommand
from .assistant_tool_api import AssistantInternalToolsView
from .test_assistant_tools import DEPLOYMENT, SERVICE_TOKEN, ReceiptToolFixture

urlpatterns = [
    path('api/cangxu/assistant/internal/tools/', AssistantInternalToolsView.as_view())
]


urlpatterns.append(path('', include('InvenTree.urls')))


@skipUnless(
    shutil.which('node')
    and (
        Path(__file__).resolve().parents[3]
        / 'assistant/node_modules/@earendil-works/pi-durable/package.json'
    ).exists(),
    'Pi integration requires Node 24 and npm ci in src/assistant; Assistant CI installs both',
)
@override_settings(USE_TZ=True, ROOT_URLCONF=__name__, ALLOWED_HOSTS=['*'])
class ReceiptRuntimeIntegrationTests(ReceiptToolFixture, LiveServerTestCase):
    """Use real HTTP, actual Pi storage and actual Django domain transactions."""

    def setUp(self):
        """Start the actual isolated Node service; no model or real data is sent."""
        self.build_fixture()
        self.state = tempfile.TemporaryDirectory(prefix='cangxu-pi-integration-')
        self.addCleanup(self.state.cleanup)
        self.envpatch = patch.dict(
            os.environ,
            {
                'ASSISTANT_RUNTIME_TOKEN': SERVICE_TOKEN,
                'ASSISTANT_DEPLOYMENT_ID': DEPLOYMENT,
            },
        )
        self.envpatch.start()
        self.addCleanup(self.envpatch.stop)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            self.port = sock.getsockname()[1]
        self.process = None
        self.addCleanup(self.stop_runtime)
        self.start_runtime()

    def start_runtime(self):
        """Start a new process over the same server-generated SQLite storage."""
        root = Path(__file__).resolve().parents[3] / 'assistant'
        env = {
            **os.environ,
            'ASSISTANT_PORT': str(self.port),
            'ASSISTANT_STORAGE_DIR': self.state.name,
            'ASSISTANT_MODEL_PROVIDER': 'fixture',
            'ASSISTANT_DJANGO_URL': self.live_server_url,
        }
        env.update(getattr(self, 'model_env', {}))
        self.process = subprocess.Popen(
            [shutil.which('node'), 'src/server.ts'],
            cwd=root,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        ready, _, _ = select.select([self.process.stdout], [], [], 10)
        self.assertTrue(ready, 'Pi service did not start within 10 seconds')
        line = self.process.stdout.readline()
        self.assertTrue(line, 'Pi service exited before readiness')
        self.assertTrue(json.loads(line)['ready'])

    def stop_runtime(self, kill=False):
        """Release the exact test child and its streams, including on assertion failure."""
        if self.process:
            if kill:
                self.process.kill()
            else:
                self.process.terminate()
            self.process.wait(timeout=10)
            self.process.stdout.close()
            self.process.stderr.close()
            self.process = None

    def request_runtime(self, route, payload=None):
        """Send the same authenticated protocol as the Django gateway."""
        url = f'http://127.0.0.1:{self.port}/v1/partners/{self.binding.partner_id}/{route}'
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={
                'Authorization': f'Bearer {SERVICE_TOKEN}',
                'X-Assistant-Deployment': DEPLOYMENT,
                'Content-Type': 'application/json',
            },
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.load(response)

    def wait_for_task(self, task_id):
        """Bound the integration wait and report actual runtime task status."""
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            status = self.request_runtime('status')
            task = next(
                (task for task in status['recent_tasks'] if task['id'] == task_id), None
            )
            if task and task['status'] in {'completed', 'aborted', 'failed', 'faulted'}:
                return task['status']
            time.sleep(0.05)
        self.fail('Pi task did not settle before the integration deadline')

    def test_background_link_restart_and_unchanged_timer_are_real_and_quiet(self):
        """Queued work survives process death and writes one actual business association."""
        work = {
            'grant_id': self.grant.pk,
            'grant_version': 1,
            'receipt_id': str(self.receipt.pk),
            'attachments': [{'id': self.attachment.pk, 'kind': 'photo'}],
        }
        payload = {
            'key': 'fictional-event-1',
            'source': 'event',
            'dueAt': int(time.time() * 1000) + 1000,
            'work': work,
        }
        accepted = self.request_runtime('events', payload)
        self.assertEqual(accepted['status'], 'accepted')
        self.stop_runtime(kill=True)
        self.start_runtime()
        self.assertEqual(self.wait_for_task(accepted['task_id']), 'completed')
        self.assertEqual(ReceiptArchiveEvidence.objects.count(), 1)
        self.assertEqual(AssistantCommand.objects.count(), 1)
        history = self.request_runtime('messages')['items']
        self.assertEqual(len(history), 1)
        self.assertNotIn('归档完成', history[0]['text'])
        # Same delivery gets the existing durable task and no new database effect.
        self.assertEqual(
            self.request_runtime('events', payload)['task_id'], accepted['task_id']
        )
        timer = self.request_runtime(
            'events',
            {
                'key': 'fictional-duty-slot-2',
                'source': 'timer',
                'dueAt': 0,
                'work': {**work, 'attachments': []},
            },
        )
        self.assertEqual(self.wait_for_task(timer['task_id']), 'completed')
        self.assertEqual(len(self.request_runtime('messages')['items']), 1)
        self.assertEqual(ReceiptArchiveEvidence.objects.count(), 1)
        self.assertIn('inspection', self.query()['missing'])

    def test_committed_business_write_response_loss_recovers_original_command(self):
        """Kill Pi after Django commits but before the tool response arrives."""
        linked = threading.Event()
        release = threading.Event()
        original = AssistantInternalToolsView.post
        held = False

        def hold_first_response(view, request):
            nonlocal held
            result = original(view, request)
            if request.data.get('tool') == 'link_receipt_archive' and not held:
                held = True
                linked.set()
                release.wait(5)
            return result

        work = {
            'grant_id': self.grant.pk,
            'grant_version': 1,
            'receipt_id': str(self.receipt.pk),
            'attachments': [{'id': self.attachment.pk, 'kind': 'photo'}],
        }
        with patch.object(AssistantInternalToolsView, 'post', hold_first_response):
            task = self.request_runtime(
                'events',
                {
                    'key': 'fictional-response-lost',
                    'source': 'event',
                    'dueAt': 0,
                    'work': work,
                },
            )
            try:
                self.assertTrue(
                    linked.wait(10),
                    'Django did not commit the synthetic archive association',
                )
                command = AssistantCommand.objects.get()
                self.assertEqual(ReceiptArchiveEvidence.objects.count(), 1)
                self.stop_runtime(kill=True)
            finally:
                release.set()
            self.start_runtime()
            self.assertEqual(self.wait_for_task(task['task_id']), 'completed')
            self.assertEqual(AssistantCommand.objects.get().key, command.key)
            self.assertEqual(AssistantCommand.objects.count(), 1)
            self.assertEqual(ReceiptArchiveEvidence.objects.count(), 1)

    @skipUnless(
        os.environ.get('CANGXU_LIVE_MODEL_TEST') == '1',
        'Explicit synthetic self-hosted model validation only',
    )
    def test_self_hosted_model_query_action_query_and_persisted_reply(self):
        """Use the configured model with real APIs and only fictional database records."""
        from users.models import RuleSet

        from .models import CountSession

        rule = RuleSet.objects.get(group=self.user.groups.first(), name='stock')
        rule.can_add = True
        rule.save()
        read_role = RuleSet.objects.get(
            group=self.user.groups.first(), name='stock_location'
        )
        read_role.can_view = True
        read_role.save()
        config = Path(__file__).resolve().parents[3] / 'assistant' / '.env.local'
        local = dict(
            line.split('=', 1)
            for line in config.read_text().splitlines()
            if line and not line.startswith('#')
        )
        self.model_env = {
            key: local[key]
            for key in [
                'ASSISTANT_MODEL_PROVIDER',
                'ASSISTANT_MODEL_BASE_URL',
                'ASSISTANT_MODEL_API_KEY',
                'ASSISTANT_MODEL_ID',
            ]
        }
        self.model_env['ASSISTANT_MODEL_MAX_OUTPUT_TOKENS'] = '2048'
        # Use a fresh partner store so a previous fixture model never masks the live provider.
        self.stop_runtime()
        self.start_runtime()
        reference = 'FICTIONAL-LIVE-MODEL-COUNT'
        prompt = (
            'This is an authorized synthetic business integration task. Use business_capabilities to inspect the tools, '
            f'then business_query locations id {self.receipt.location_id}. '
            f'Use business_action prepare_count with data reference={reference} and location={self.receipt.location_id}. '
            'This creates a count plan only; do not record actual counts, approvals or signatures. '
            'Then business_query count_sessions using the ID returned by the action to verify the real saved record. '
            'Do not ask for additional grants or confirmation. After the successful query-action-query chain, reply '
            'SYNTHETIC_CHAIN_OK and the actual created count ID. If an API fails, report the failure accurately.'
        )
        self.request_runtime(
            'messages',
            {
                'request_id': 'fictional-live-model-chain',
                'text': prompt,
                'references': [],
            },
        )
        deadline = time.monotonic() + 180
        history = []
        while time.monotonic() < deadline:
            history = self.request_runtime('messages')['items']
            if any(
                item['role'] == 'assistant' and 'SYNTHETIC_CHAIN_OK' in item['text']
                for item in history
            ):
                break
            time.sleep(0.5)
        self.assertTrue(
            any('SYNTHETIC_CHAIN_OK' in item['text'] for item in history),
            'The real model did not finish the requested API chain',
        )
        session = CountSession.objects.get(reference=reference)
        self.assertEqual(session.started_by_id, self.user.pk)
        self.assertEqual(session.state, CountSession.State.OPEN)
        self.assertEqual(
            AssistantCommand.objects.filter(
                action='prepare_count', status='succeeded'
            ).count(),
            1,
        )
        self.assertFalse(session.lines.filter(counted_quantity__isnull=False).exists())
