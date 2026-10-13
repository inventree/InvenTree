import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { setTimeout as pause } from 'node:timers/promises';
import { createRuntimeServer } from '../src/http.ts';
const DEPLOYMENT = '11111111-1111-4111-8111-111111111111';
const FIRST = '22222222-2222-4222-8222-222222222222';
const SECOND = '33333333-3333-4333-8333-333333333333';
const TOKEN = 'synthetic-internal-token-32-characters';
async function fixture(overrides: NodeJS.ProcessEnv = {}) {
  const dir = await mkdtemp(join(tmpdir(), 'cangxu-http-'));
  const env = {
    ASSISTANT_RUNTIME_TOKEN: TOKEN,
    ASSISTANT_DEPLOYMENT_ID: DEPLOYMENT,
    ASSISTANT_STORAGE_DIR: dir,
    ...overrides
  };
  let service = await createRuntimeServer(env);
  let base = '';
  const listen = async () => {
    await new Promise<void>((resolve) =>
      service.server.listen(0, '127.0.0.1', resolve)
    );
    const address = service.server.address();
    base = `http://127.0.0.1:${typeof address === 'object' && address?.port}`;
  };
  await listen();
  return {
    async call(
      path: string,
      input?: unknown,
      headers?: Record<string, string>
    ) {
      const result = await fetch(`${base}/v1/partners/${path}`, {
        method: input === undefined ? 'GET' : 'POST',
        headers: headers ?? {
          Authorization: `Bearer ${TOKEN}`,
          'X-Assistant-Deployment': DEPLOYMENT,
          'Content-Type': 'application/json'
        },
        body: input === undefined ? undefined : JSON.stringify(input)
      });
      return { status: result.status, data: await result.json() };
    },
    async restart() {
      await service.close();
      service = await createRuntimeServer(env);
      await listen();
    },
    async close() {
      await service.close();
      await rm(dir, { recursive: true, force: true });
    }
  };
}
test('authenticated runtime has isolated persisted histories and durable request conflict', async () => {
  const f = await fixture();
  try {
    assert.equal((await f.call(`${FIRST}/status`, undefined, {})).status, 401);
    assert.equal(
      (
        await f.call(`${FIRST}/status`, undefined, {
          Authorization: `Bearer ${TOKEN}`,
          'X-Assistant-Deployment': SECOND
        })
      ).status,
      403
    );
    assert.equal((await f.call('invalid/status')).status, 400);
    const accepted = await f.call(`${FIRST}/messages`, {
      request_id: 'message-1',
      text: 'Synthetic first user',
      references: []
    });
    assert.equal(accepted.status, 202);
    const duplicate = await f.call(`${FIRST}/messages`, {
      request_id: 'message-1',
      text: 'Synthetic first user'
    });
    assert.equal(duplicate.data.submission_id, accepted.data.submission_id);
    assert.equal(
      (
        await f.call(`${FIRST}/messages`, {
          request_id: 'message-1',
          text: 'Different input'
        })
      ).status,
      409
    );
    assert.deepEqual((await f.call(`${SECOND}/messages`)).data.items, []);
    let history: { items: { id: number; role: string; text: string }[] } = {
      items: []
    };
    for (let i = 0; i < 30; i++) {
      history = (await f.call(`${FIRST}/messages`)).data;
      if (
        history.items.some(
          (item: { role: string }) => item.role === 'assistant'
        )
      )
        break;
      await pause(10);
    }
    assert.deepEqual(
      history.items.map((item: { role: string }) => item.role),
      ['user', 'assistant']
    );
    assert.equal(history.items[0].text, 'Synthetic first user');
    const latest = (await f.call(`${FIRST}/messages?limit=1`)).data;
    const older = (
      await f.call(`${FIRST}/messages?limit=1&before=${latest.next_before}`)
    ).data;
    assert.equal(older.items[0].role, 'user');
    assert.equal((await f.call(`${FIRST}/messages?limit=1000`)).status, 400);
    assert.equal(
      (
        await f.call(`${FIRST}/messages`, {
          request_id: 'too-big',
          text: 'x'.repeat(70000)
        })
      ).status,
      413
    );
    assert.equal(
      (
        await f.call(`${FIRST}/messages`, {
          request_id: 'refs',
          text: 'query',
          references: [{ object_id: 1 }]
        })
      ).status,
      400
    );
    await f.restart();
    const recovered = await f.call(`${FIRST}/messages`, {
      request_id: 'message-1',
      text: 'Synthetic first user'
    });
    assert.equal(recovered.data.submission_id, accepted.data.submission_id);
    assert.deepEqual(
      (await f.call(`${FIRST}/messages`)).data.items,
      history.items
    );
    assert.deepEqual((await f.call(`${SECOND}/messages`)).data.items, []);
  } finally {
    await f.close();
  }
});
test('startup resumes known partner event work without browser request', async () => {
  const f = await fixture();
  try {
    const event = {
      key: 'synthetic-event-1',
      source: 'event',
      dueAt: Date.now() + 200
    };
    const accepted = await f.call(`${FIRST}/events`, event);
    assert.equal(accepted.status, 202);
    assert.equal(accepted.data.execution, 'synthetic_check_only');
    await f.restart();
    await pause(250);
    const state = (await f.call(`${FIRST}/status`)).data;
    assert.equal(state.pending_tasks, 0);
    const again = await f.call(`${FIRST}/events`, event);
    assert.equal(again.data.task_id, accepted.data.task_id);
    assert.equal(
      (await f.call(`${FIRST}/events`, { ...event, dueAt: event.dueAt + 1 }))
        .status,
      409
    );
    assert.equal(
      (
        await f.call(`${FIRST}/controls`, {
          request_id: 'stop-1',
          scope: 'all-background'
        })
      ).status,
      200
    );
    await f.restart();
    assert.equal(
      (
        await f.call(`${FIRST}/events`, {
          key: 'event2',
          source: 'event',
          dueAt: 0
        })
      ).status,
      409
    );
  } finally {
    await f.close();
  }
});

test('model timeout becomes a visible persisted failure instead of silent idle', async () => {
  const upstream = createServer(() => {});
  await new Promise<void>((resolve) =>
    upstream.listen(0, '127.0.0.1', resolve)
  );
  const address = upstream.address();
  const f = await fixture({
    ASSISTANT_MODEL_PROVIDER: 'openai-compatible',
    ASSISTANT_MODEL_BASE_URL: `http://127.0.0.1:${typeof address === 'object' && address?.port}/v1`,
    ASSISTANT_MODEL_ID: 'synthetic-slow-model',
    ASSISTANT_MODEL_API_KEY: 'synthetic-key-must-not-appear',
    ASSISTANT_MODEL_TIMEOUT_MS: '50'
  });
  try {
    await f.call(`${FIRST}/messages`, {
      request_id: 'slow-input',
      text: 'Synthetic query'
    });
    let history: any;
    for (let i = 0; i < 100; i++) {
      history = (await f.call(`${FIRST}/messages`)).data;
      if (
        history.items.some((item: any) =>
          item.text.includes('模型服务请求超时')
        )
      )
        break;
      await pause(20);
    }
    assert.equal(history.items.at(-1).role, 'assistant');
    assert.match(history.items.at(-1).text, /模型服务请求超时/);
    assert.doesNotMatch(
      JSON.stringify(history),
      /synthetic-key-must-not-appear/
    );
    await f.restart();
    assert.match(
      (await f.call(`${FIRST}/messages`)).data.items.at(-1).text,
      /你的消息已保留/
    );
  } finally {
    await f.close();
    upstream.closeAllConnections();
    await new Promise<void>((resolve) => upstream.close(() => resolve()));
  }
});
