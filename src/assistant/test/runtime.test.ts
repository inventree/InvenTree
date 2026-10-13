import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createInterface } from 'node:readline';
import { test } from 'node:test';
import { context, openRuntime } from '../src/runtime.ts';

async function fixture() {
  const dir = await mkdtemp(join(tmpdir(), 'cangxu-s0-'));
  return { dir, file: join(dir, 'session.sqlite') };
}
test('actual Pi SQLite input dedupe, detached background event/timer, scoped persistent stop', async () => {
  const { dir, file } = await fixture();
  let runtime = await openRuntime(file);
  try {
    await assert.rejects(openRuntime(file), /already has an owner/);
    const first = await runtime.root.submit(
      {
        type: 'input',
        content: 'Synthetic receipt query',
        requestId: 'input-1'
      },
      context
    );
    const duplicate = await runtime.root.submit(
      {
        type: 'input',
        content: 'Synthetic receipt query',
        requestId: 'input-1'
      },
      context
    );
    assert.equal(first.id, duplicate.id);
    assert.equal((await first.wait(context)).status, 'done');
    const event = {
      key: 'event:fake-1',
      source: 'event' as const,
      dueAt: Date.now() + 150
    };
    const task = await runtime.deliver(event);
    assert.equal(await runtime.deliver(event), task);
    await assert.rejects(
      runtime.deliver({ ...event, dueAt: event.dueAt + 1 }),
      /different content/
    );
    await runtime.control('stop-reply', 'reply');
    assert.equal(
      (await runtime.harness.waitForTask(task, context)).state.outcome.status,
      'completed'
    );
    const timer = await runtime.deliver({
      key: 'duty:fake-1:slot:1:rev:1',
      source: 'timer',
      dueAt: Date.now() + 5000
    });
    await runtime.control('stop-task', 'task', timer);
    assert.equal(
      (await runtime.harness.waitForTask(timer, context)).state.outcome.status,
      'aborted'
    );
    await runtime.deliver({
      key: 'event:fake-2',
      source: 'event',
      dueAt: Date.now() + 5000
    });
    await runtime.control('stop-all', 'all-background');
    await runtime.close();
    runtime = await openRuntime(file);
    await runtime.control('stop-all', 'all-background');
    await assert.rejects(
      runtime.deliver({
        key: 'event:fake-3',
        source: 'event',
        dueAt: Date.now()
      }),
      /persistently stopped/
    );
    assert.deepEqual((await runtime.snapshot())!.completed, [event.key]);
    const again = await runtime.root.submit(
      {
        type: 'input',
        content: 'Synthetic receipt query',
        requestId: 'input-1'
      },
      context
    );
    assert.equal(again.id, first.id);
  } finally {
    await runtime.close();
    await rm(dir, { recursive: true, force: true });
  }
});

test(
  'SIGKILL recovery reopens exclusive ownership and resumes the same pending task once',
  { timeout: 10000 },
  async () => {
    const { dir, file } = await fixture();
    const child = spawn(process.execPath, ['src/worker.ts', file], {
      cwd: new URL('..', import.meta.url),
      stdio: ['pipe', 'pipe', 'pipe']
    });
    const lines = createInterface({ input: child.stdout })[
      Symbol.asyncIterator
    ]();
    try {
      assert.equal(JSON.parse((await lines.next()).value!).ready, true);
      const delivery = {
        key: 'event:crash-fixture',
        source: 'event' as const,
        dueAt: Date.now() + 500
      };
      child.stdin.write(
        `${JSON.stringify({ action: 'deliver', input: delivery })}\n`
      );
      const id = JSON.parse((await lines.next()).value!).task;
      assert.equal(typeof id, 'number');
      const exited = once(child, 'exit');
      child.kill('SIGKILL');
      await exited;
      const runtime = await openRuntime(file);
      try {
        assert.equal(await runtime.deliver(delivery), id);
        assert.equal(
          (await runtime.harness.waitForTask(id, context)).state.outcome.status,
          'completed'
        );
        assert.deepEqual((await runtime.snapshot())!.completed, [delivery.key]);
      } finally {
        await runtime.close();
      }
    } finally {
      child.kill();
      await rm(dir, { recursive: true, force: true });
    }
  }
);

test('stop qualification survives interruption before the Pi abort mark', async () => {
  const { dir, file } = await fixture();
  let runtime = await openRuntime(file);
  try {
    const task = await runtime.deliver({
      key: 'event:stop-gap',
      source: 'event',
      dueAt: Date.now() + 150
    });
    runtime.harness.abortTask = async () => {
      throw new Error('simulated process interruption before abort');
    };
    await assert.rejects(
      runtime.control('stop-gap', 'task', task),
      /simulated process interruption/
    );
    await runtime.close();
    runtime = await openRuntime(file);
    assert.equal(
      (await runtime.harness.waitForTask(task, context)).state.outcome.status,
      'aborted'
    );
    assert.deepEqual((await runtime.snapshot())!.completed, []);
  } finally {
    await runtime.close();
    await rm(dir, { recursive: true, force: true });
  }
});

test('configuration failure releases ownership and symlink aliases share ownership', async () => {
  const { dir, file } = await fixture();
  try {
    await assert.rejects(
      openRuntime(file, { ASSISTANT_MODEL_PROVIDER: 'unsupported' }),
      /Unsupported/
    );
    const runtime = await openRuntime(file);
    try {
      const { symlink } = await import('node:fs/promises');
      const alias = join(dir, 'alias.sqlite');
      await symlink(file, alias);
      await assert.rejects(openRuntime(alias), /already has an owner/);
    } finally {
      await runtime.close();
    }
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('provider output limits are validated and idle existing roots apply host-selected model', async () => {
  const { configuredModels } = await import('../src/provider.ts');
  const env = {
    ASSISTANT_MODEL_PROVIDER: 'openai-compatible',
    ASSISTANT_MODEL_BASE_URL: 'http://127.0.0.1:9/v1',
    ASSISTANT_MODEL_API_KEY: 'fixture-key-unused',
    ASSISTANT_MODEL_ID: 'fixture-live-model'
  };
  for (const value of ['0', '-1', 'NaN', 'Infinity', '1.5'])
    assert.throws(
      () =>
        configuredModels({ ...env, ASSISTANT_MODEL_MAX_OUTPUT_TOKENS: value }),
      /positive integer/
    );
  const configured = configuredModels({
    ...env,
    ASSISTANT_MODEL_MAX_OUTPUT_TOKENS: '9000'
  });
  assert.equal(
    configured.models.getModel('cangxu-compatible', 'fixture-live-model')
      ?.maxTokens,
    8192
  );
  const { dir, file } = await fixture();
  let runtime = await openRuntime(file);
  try {
    assert.equal((await runtime.root.agent(context)).model?.provider, 'faux');
    await runtime.close();
    runtime = await openRuntime(file, env);
    assert.deepEqual((await runtime.root.agent(context)).model, {
      provider: 'cangxu-compatible',
      modelId: 'fixture-live-model'
    });
  } finally {
    await runtime.close();
    await rm(dir, { recursive: true, force: true });
  }
});
