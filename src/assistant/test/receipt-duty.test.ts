import assert from 'node:assert/strict';
import { once } from 'node:events';
import { mkdtemp, rm } from 'node:fs/promises';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { context, openRuntime } from '../src/runtime.ts';
test('pinned receipt duty links explicit archive evidence, waits truthfully and suppresses unchanged notices', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'cangxu-receipt-duty-'));
  const calls: Record<string, unknown>[] = [];
  let status = 'waiting';
  const backend = createServer(async (request, response) => {
    assert.equal(
      request.headers.authorization,
      'Bearer synthetic-service-token'
    );
    assert.equal(
      request.headers['x-assistant-deployment'],
      'synthetic-deployment'
    );
    let text = '';
    for await (const chunk of request) text += chunk;
    const call = JSON.parse(text);
    calls.push(call);
    assert.equal(call.partner_id, 'synthetic-partner');
    assert.equal(call.grant_id, 42);
    assert.equal(call.grant_version, 3);
    assert.equal(call.object_id, 'synthetic-receipt');
    assert.match(call.command_id, /^receipt:[a-f0-9]{64}$/);
    response.setHeader('Content-Type', 'application/json');
    response.end(
      JSON.stringify(
        call.tool === 'receipt_status'
          ? {
              status,
              missing: status === 'waiting' ? ['signed_acceptance'] : []
            }
          : { status: 'linked' }
      )
    );
  });
  await new Promise<void>((resolve) => backend.listen(0, '127.0.0.1', resolve));
  const address = backend.address();
  const runtime = await openRuntime(join(dir, 'session.sqlite'), {
    ASSISTANT_DJANGO_URL: `http://127.0.0.1:${typeof address === 'object' && address?.port}`,
    ASSISTANT_RUNTIME_TOKEN: 'synthetic-service-token',
    ASSISTANT_DEPLOYMENT_ID: 'synthetic-deployment',
    ASSISTANT_PARTNER_ID: 'synthetic-partner'
  });
  const work = {
    grant_id: 42,
    grant_version: 3,
    receipt_id: 'synthetic-receipt',
    attachments: [{ id: 7, kind: 'photo' as const }]
  };
  try {
    const first = await runtime.deliver({
      key: 'event-receipt-1',
      source: 'event',
      dueAt: 0,
      work
    });
    const firstResult = await runtime.harness.waitForTask(first, context);
    assert.equal(firstResult.state.outcome.status, 'completed');
    assert.equal(calls.length, 2);
    assert.equal(calls[0].tool, 'link_receipt_archive');
    assert.equal(calls[1].tool, 'receipt_status');
    assert.deepEqual(calls[0].args, { attachment_id: 7, kind: 'photo' });
    const second = await runtime.deliver({
      key: 'timer-receipt-1',
      source: 'timer',
      dueAt: 0,
      work: { ...work, attachments: [] }
    });
    await runtime.harness.waitForTask(second, context);
    let notices = (
      await runtime.root.entries({}, 100, undefined, context)
    ).items.filter((entry) => entry.kind === 'cangxu.notice');
    assert.equal(notices.length, 1);
    assert.match(JSON.stringify(notices[0].data), /验收签字/);
    status = 'ready';
    const third = await runtime.deliver({
      key: 'event-receipt-2',
      source: 'event',
      dueAt: 0,
      work: { ...work, attachments: [] }
    });
    await runtime.harness.waitForTask(third, context);
    notices = (
      await runtime.root.entries({}, 100, undefined, context)
    ).items.filter((entry) => entry.kind === 'cangxu.notice');
    assert.equal(notices.length, 2);
  } finally {
    await runtime.close();
    await new Promise<void>((resolve) => backend.close(() => resolve()));
    await rm(dir, { recursive: true, force: true });
  }
});

test(
  'receipt link restart reuses the same command after backend accepted but response was lost',
  { timeout: 10000 },
  async () => {
    const { spawn } = await import('node:child_process');
    const { createInterface } = await import('node:readline');
    const dir = await mkdtemp(join(tmpdir(), 'cangxu-receipt-recovery-'));
    const commandIds: string[] = [];
    const effects = new Set<string>();
    let resolveLinked: (() => void) | undefined;
    const linked = new Promise<void>((resolve) => {
      resolveLinked = resolve;
    });
    const backend = createServer(async (request, response) => {
      let text = '';
      for await (const chunk of request) text += chunk;
      const call = JSON.parse(text);
      if (call.tool === 'link_receipt_archive') {
        commandIds.push(call.command_id);
        effects.add(call.command_id);
        if (commandIds.length === 1) {
          resolveLinked!();
          return;
        }
      }
      response.end(
        JSON.stringify(
          call.tool === 'receipt_status'
            ? { status: 'ready', missing: [] }
            : { status: 'linked' }
        )
      );
    });
    await new Promise<void>((resolve) =>
      backend.listen(0, '127.0.0.1', resolve)
    );
    const address = backend.address();
    const file = join(dir, 'session.sqlite');
    const env = {
      ASSISTANT_DJANGO_URL: `http://127.0.0.1:${typeof address === 'object' && address?.port}`,
      ASSISTANT_RUNTIME_TOKEN: 'synthetic-service-token',
      ASSISTANT_DEPLOYMENT_ID: 'synthetic-deployment',
      ASSISTANT_PARTNER_ID: 'synthetic-partner'
    };
    // Worker accepts env only for deterministic business-task adapter; fixture model remains default.
    const child = spawn(process.execPath, ['src/worker.ts', file], {
      cwd: new URL('..', import.meta.url),
      env: { ...process.env, ...env },
      stdio: ['pipe', 'pipe', 'pipe']
    });
    const lines = createInterface({ input: child.stdout })[
      Symbol.asyncIterator
    ]();
    try {
      await lines.next();
      const delivery = {
        key: 'receipt-restart',
        source: 'event' as const,
        dueAt: 0,
        work: {
          grant_id: 42,
          grant_version: 1,
          receipt_id: 'synthetic-receipt',
          attachments: [{ id: 7, kind: 'photo' as const }]
        }
      };
      child.stdin.write(
        `${JSON.stringify({ action: 'deliver', input: delivery })}\n`
      );
      const id = JSON.parse((await lines.next()).value!).task;
      await linked;
      const exited = once(child, 'exit');
      child.kill('SIGKILL');
      await exited;
      const runtime = await openRuntime(file, env);
      try {
        assert.equal(
          (await runtime.harness.waitForTask(id, context)).state.outcome.status,
          'completed'
        );
      } finally {
        await runtime.close();
      }
      assert.equal(commandIds.length, 2);
      assert.equal(commandIds[0], commandIds[1]);
      assert.equal(effects.size, 1);
    } finally {
      child.kill();
      backend.closeAllConnections();
      await new Promise<void>((resolve) => backend.close(() => resolve()));
      await rm(dir, { recursive: true, force: true });
    }
  }
);

test('business retry keeps one command identity and permanent denial becomes one persisted notice', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'cangxu-receipt-retry-'));
  const ids: string[] = [];
  let denied = false;
  let calls = 0;
  const backend = createServer(async (request, response) => {
    let text = '';
    for await (const chunk of request) text += chunk;
    const call = JSON.parse(text);
    calls++;
    if (denied) {
      response.writeHead(403);
      response.end('{}');
      return;
    }
    if (call.tool === 'link_receipt_archive') {
      ids.push(call.command_id);
      if (ids.length === 1) {
        response.writeHead(500);
        response.end('{}');
        return;
      }
    }
    response.end(
      JSON.stringify(
        call.tool === 'receipt_status'
          ? { status: 'waiting', missing: ['warehouse_signature'] }
          : { status: 'linked' }
      )
    );
  });
  await new Promise<void>((resolve) => backend.listen(0, '127.0.0.1', resolve));
  const address = backend.address();
  const runtime = await openRuntime(join(dir, 'session.sqlite'), {
    ASSISTANT_DJANGO_URL: `http://127.0.0.1:${typeof address === 'object' && address?.port}`,
    ASSISTANT_RUNTIME_TOKEN: 'synthetic-service-token',
    ASSISTANT_DEPLOYMENT_ID: 'synthetic-deployment',
    ASSISTANT_PARTNER_ID: 'synthetic-partner'
  });
  const work = {
    grant_id: 42,
    grant_version: 1,
    receipt_id: 'synthetic-receipt',
    attachments: [{ id: 7, kind: 'photo' as const }]
  };
  try {
    const task = await runtime.deliver({
      key: 'event-retry',
      source: 'event',
      dueAt: 0,
      work
    });
    assert.equal(
      (await runtime.harness.waitForTask(task, context)).state.outcome.status,
      'completed'
    );
    assert.equal(ids.length, 2);
    assert.equal(ids[0], ids[1]);
    const again = await runtime.deliver({
      key: 'timer-same-association',
      source: 'timer',
      dueAt: 0,
      work
    });
    await runtime.harness.waitForTask(again, context);
    assert.equal(ids[2], ids[0]);
    denied = true;
    const before = calls;
    for (const key of ['event-denied', 'timer-denied']) {
      const failed = await runtime.deliver({
        key,
        source: 'event',
        dueAt: 0,
        work: { ...work, attachments: [] }
      });
      assert.equal(
        (await runtime.harness.waitForTask(failed, context)).state.outcome
          .status,
        'failed'
      );
    }
    assert.equal(calls, before + 2);
    const notices = (
      await runtime.root.entries({}, 100, undefined, context)
    ).items.filter((entry) => entry.kind === 'cangxu.notice');
    assert.equal(notices.length, 2);
    assert.ok(
      notices.some((entry) => JSON.stringify(entry.data).includes('仓管签字'))
    );
    assert.ok(
      notices.some((entry) => JSON.stringify(entry.data).includes('暂未完成'))
    );
  } finally {
    await runtime.close();
    backend.closeAllConnections();
    await new Promise<void>((resolve) => backend.close(() => resolve()));
    await rm(dir, { recursive: true, force: true });
  }
});
