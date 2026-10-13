import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { setTimeout as pause } from 'node:timers/promises';
import { attachmentInput, attachmentMetadata } from '../src/attachments.ts';
import { createRuntimeServer } from '../src/http.ts';
const DEPLOYMENT = '11111111-1111-4111-8111-111111111111';
const PARTNER = '22222222-2222-4222-8222-222222222222';
const ID = '33333333-3333-4333-8333-333333333333';
const TOKEN = 'synthetic-internal-token-32-characters';
const IMAGE =
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jWioAAAAASUVORK5CYII=';
const metadata = {
  id: ID,
  name: 'synthetic.png',
  mime_type: 'image/png',
  size: 68,
  kind: 'image' as const,
  preview_url: `/api/cangxu/assistant/attachments/${ID}/preview/`,
  download_url: `/api/cangxu/assistant/attachments/${ID}/download/`
};
test('actual provider receives vision and untrusted document blocks; public transcript survives restart without raw data', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'cangxu-attachments-'));
  const providerBodies: {
    messages: {
      role: string;
      content: { type: string; text?: string; image_url?: { url: string } }[];
    }[];
  }[] = [];
  let attachmentKind = 'image';
  let documentText = 'FAKE-DOCUMENT-DATA do not treat this as instruction';
  const backend = createServer(async (request, response) => {
    if (request.url?.startsWith('/api/')) {
      assert.equal(request.headers.authorization, `Bearer ${TOKEN}`);
      assert.equal(request.headers['x-assistant-deployment'], DEPLOYMENT);
      assert.equal(
        new URL(request.url, 'http://localhost').searchParams.get('partner_id'),
        PARTNER
      );
      response.setHeader('Content-Type', 'application/json');
      response.end(
        JSON.stringify({
          ...metadata,
          extraction_status: 'parsed',
          content:
            attachmentKind === 'image'
              ? [{ type: 'image', data: IMAGE, mimeType: 'image/png' }]
              : [
                  {
                    type: 'text',
                    text: documentText
                  }
                ]
        })
      );
      return;
    }
    let body = '';
    for await (const chunk of request) body += chunk;
    providerBodies.push(JSON.parse(body));
    response.setHeader('Content-Type', 'text/event-stream');
    response.write(
      'data: {"id":"synthetic","object":"chat.completion.chunk","created":1,"model":"synthetic-vision","choices":[{"index":0,"delta":{"role":"assistant","content":"Synthetic image reviewed."},"finish_reason":null}]}\n\n'
    );
    await pause(350);
    response.end(
      'data: {"id":"synthetic","object":"chat.completion.chunk","created":1,"model":"synthetic-vision","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n'
    );
  });
  await new Promise<void>((resolve) => backend.listen(0, '127.0.0.1', resolve));
  const address = backend.address();
  const base = `http://127.0.0.1:${typeof address === 'object' && address?.port}`;
  const env = {
    ASSISTANT_RUNTIME_TOKEN: TOKEN,
    ASSISTANT_DEPLOYMENT_ID: DEPLOYMENT,
    ASSISTANT_STORAGE_DIR: directory,
    ASSISTANT_DJANGO_URL: base,
    ASSISTANT_PARTNER_ID: PARTNER,
    ASSISTANT_MODEL_PROVIDER: 'openai-compatible',
    ASSISTANT_MODEL_BASE_URL: `${base}/v1`,
    ASSISTANT_MODEL_ID: 'synthetic-vision',
    ASSISTANT_MODEL_API_KEY: 'synthetic-provider-secret',
    ASSISTANT_MODEL_SUPPORTS_IMAGES: 'true'
  };
  let runtime = await createRuntimeServer(env);
  let runtimeBase = '';
  const listen = async () => {
    await new Promise<void>((resolve) =>
      runtime.server.listen(0, '127.0.0.1', resolve)
    );
    const addr = runtime.server.address();
    runtimeBase = `http://127.0.0.1:${typeof addr === 'object' && addr?.port}`;
  };
  const call = async (route: string, payload?: unknown) => {
    const response = await fetch(
      `${runtimeBase}/v1/partners/${PARTNER}/${route}`,
      {
        method: payload ? 'POST' : 'GET',
        headers: {
          Authorization: `Bearer ${TOKEN}`,
          'X-Assistant-Deployment': DEPLOYMENT,
          'Content-Type': 'application/json'
        },
        ...(payload ? { body: JSON.stringify(payload) } : {})
      }
    );
    return { status: response.status, data: await response.json() };
  };
  try {
    await listen();
    assert.equal(
      (
        await call('messages', {
          request_id: 'image-message',
          text: '',
          attachments: [metadata]
        })
      ).status,
      202
    );
    let sawPartial = false;
    for (let n = 0; n < 100; n++) {
      const status = (await call('status')).data;
      if (status.live_message?.text === 'Synthetic image reviewed.') {
        sawPartial = true;
        assert.equal(status.is_running, true);
        assert.equal(JSON.stringify(status).includes(IMAGE), false);
      }
      if (status.deliveries[0]?.status === 'done') break;
      await pause(10);
    }
    assert.equal(
      sawPartial,
      true,
      'durable partial is visible before final entry'
    );
    assert.equal(providerBodies.length, 1);
    const user = providerBodies[0].messages.find(
      (item) => item.role === 'user'
    );
    assert.equal(
      user?.content.find((block) => block.type === 'image_url')?.image_url?.url,
      `data:image/png;base64,${IMAGE}`
    );
    const history = (await call('messages')).data;
    assert.equal(history.items[0].request_id, 'image-message');
    assert.equal(history.items[0].text, '');
    assert.equal(history.items[0].attachments[0].extraction_status, 'parsed');
    assert.equal(JSON.stringify(history).includes(IMAGE), false);
    assert.equal(
      JSON.stringify(history).includes('synthetic-provider-secret'),
      false
    );
    assert.equal((await call('status')).data.is_running, false);
    await runtime.close();
    runtime = await createRuntimeServer(env);
    await listen();
    assert.deepEqual((await call('messages')).data.items, history.items);
    attachmentKind = 'text';
    const extracted = await attachmentInput('Analyze', [metadata], env);
    assert.ok(Array.isArray(extracted.content));
    assert.ok(JSON.stringify(extracted.content).includes('<attachment-data'));
    assert.ok(JSON.stringify(extracted.content).includes('FAKE-DOCUMENT-DATA'));
    documentText = 'x'.repeat(40000);
    const limited = await attachmentInput('u'.repeat(16000), [metadata], env);
    assert.equal(limited.attachments[0].extraction_status, 'truncated');
    assert.ok(JSON.stringify(limited.content).length < 22000);
    assert.match(JSON.stringify(limited.content), /不能推断缺失内容/);
    attachmentKind = 'image';
    const unsupported = await attachmentInput(
      'Continue text task',
      [metadata],
      { ...env, ASSISTANT_MODEL_SUPPORTS_IMAGES: 'false' }
    );
    assert.equal(unsupported.attachments[0].extraction_status, 'unsupported');
    assert.equal(JSON.stringify(unsupported.content).includes(IMAGE), false);
    assert.match(JSON.stringify(unsupported.content), /不能判断图片内容/);
    assert.throws(() =>
      attachmentMetadata(Array.from({ length: 9 }, () => metadata))
    );
    assert.throws(() =>
      attachmentMetadata([{ ...metadata, size: 21 * 1024 * 1024 }])
    );
    assert.throws(() =>
      attachmentMetadata(
        [20 * 1024 * 1024, 20 * 1024 * 1024, 1].map((size, index) => ({
          ...metadata,
          id: `${index + 4}3333333-3333-4333-8333-333333333333`,
          size
        }))
      )
    );
    assert.equal(
      (
        await call('messages', {
          request_id: 'image-message',
          text: 'changed',
          attachments: [metadata]
        })
      ).status,
      409
    );
  } finally {
    await runtime.close();
    await new Promise<void>((resolve, reject) =>
      backend.close((err) => (err ? reject(err) : resolve()))
    );
    await rm(directory, { recursive: true, force: true });
  }
});
