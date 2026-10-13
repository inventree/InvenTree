import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import {
  fauxAssistantMessage,
  fauxToolCall
} from '@earendil-works/pi-ai/providers/faux';
import { context, openRuntime } from '../src/runtime.ts';

test('real Pi tool intent -> current-user Django bridge -> tool result -> persisted model answer', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'cangxu-model-tools-'));
  const calls: Record<string, unknown>[] = [];
  const effects = new Set<string>();
  let actionAttempts = 0;
  const backend = createServer(async (request, response) => {
    assert.equal(request.url, '/api/cangxu/assistant/internal/business-tools/');
    assert.equal(request.headers.authorization, 'Bearer fixture-service-token');
    assert.equal(
      request.headers['x-assistant-deployment'],
      'fixture-deployment'
    );
    let text = '';
    for await (const chunk of request) text += chunk;
    const call = JSON.parse(text);
    calls.push(call);
    assert.equal(call.partner_id, 'fixture-partner');
    assert.equal(call.grant_id, undefined);
    assert.equal(call.user_id, undefined);
    assert.match(call.command_id, /^model:[a-f0-9]{64}$/);
    assert.equal(typeof call.run_id, 'string');
    assert.equal(typeof call.step_id, 'string');
    if (call.tool === 'business_action') {
      effects.add(call.command_id);
      actionAttempts++;
      if (actionAttempts === 1) {
        request.socket.destroy();
        return;
      }
    }
    response.setHeader('Content-Type', 'application/json');
    response.end(
      JSON.stringify(
        call.tool === 'business_query'
          ? {
              status: 'ok',
              items: [{ id: 5, serial: 'FAKE-SN-001', quantity: 2 }]
            }
          : call.tool === 'business_action'
            ? { status: 'executed', command_receipt_id: 77 }
            : call.tool === 'business_capabilities'
              ? { status: 'ok', operations: ['prepare_count'] }
              : {
                  status: 'ok',
                  sources: [
                    {
                      process_id: 'IN-01',
                      revision: 'fixture-v1',
                      supported: false
                    }
                  ]
                }
      )
    );
  });
  await new Promise<void>((resolve) => backend.listen(0, '127.0.0.1', resolve));
  const address = backend.address();
  const runtime = await openRuntime(
    join(dir, 'session.sqlite'),
    {
      ASSISTANT_DJANGO_URL: `http://127.0.0.1:${typeof address === 'object' && address?.port}`,
      ASSISTANT_RUNTIME_TOKEN: 'fixture-service-token',
      ASSISTANT_DEPLOYMENT_ID: 'fixture-deployment',
      ASSISTANT_PARTNER_ID: 'fixture-partner',
      ASSISTANT_MAX_TOOL_CALLS_PER_INPUT: '12'
    },
    {
      fixtureResponses: [
        fauxAssistantMessage(
          [
            fauxToolCall(
              'business_query',
              {
                resource: 'stock',
                search: 'FAKE-SN-001',
                filters: { IPN: 'FAKE-IPN', aliasipn: 'FAKE-ALIAS' },
                limit: 5,
                offset: 0
              },
              { id: 'stock-query-1' }
            ),
            fauxToolCall(
              'workflow_knowledge',
              { query: '入库归档', process_id: 'IN-01' },
              { id: 'knowledge-1' }
            )
          ],
          { stopReason: 'toolUse' }
        ),
        fauxAssistantMessage(
          '虚构测试：库存查询返回数量 2；流程目录 IN-01 尚待完整支持。'
        ),
        fauxAssistantMessage(
          [
            fauxToolCall('business_capabilities', {}, { id: 'capability-1' }),
            fauxToolCall(
              'business_action',
              { operation: 'prepare_count', data: { location: 1 } },
              { id: 'action-1' }
            ),
            fauxToolCall(
              'business_action',
              { data: { location: 1 }, operation: 'prepare_count' },
              { id: 'action-retry-new-call' }
            )
          ],
          { stopReason: 'toolUse' }
        ),
        fauxAssistantMessage('虚构测试：盘点准备回执77，未代替实盘。'),
        fauxAssistantMessage(
          [
            fauxToolCall(
              'business_action',
              { operation: 'prepare_count', data: { location: 1 } },
              { id: 'action-next-user-input' }
            )
          ],
          { stopReason: 'toolUse' }
        ),
        fauxAssistantMessage('虚构测试：新交办单独准备盘点。'),
        fauxAssistantMessage(
          Array.from({ length: 13 }, (_, i) =>
            fauxToolCall(
              'business_query',
              { resource: 'parts' },
              { id: `budget-${i}` }
            )
          ),
          { stopReason: 'toolUse' }
        )
      ]
    }
  );
  try {
    const submission = await runtime.submitMessage(
      'fixture-user-command',
      '查询虚构 SN 并说明入库流程'
    );
    assert.equal((await submission.wait(context)).status, 'done');
    assert.equal(calls.length, 2);
    assert.equal(calls[0].tool, 'business_query');
    assert.equal(calls[1].tool, 'workflow_knowledge');
    const entries = (await runtime.root.entries({}, 100, undefined, context))
      .items;
    const tools = entries.filter((entry) => entry.kind === 'pi.tool-result');
    assert.equal(tools.length, 2);
    assert.match(JSON.stringify(tools), /FAKE-SN-001/);
    assert.match(JSON.stringify(tools), /fixture-v1/);
    assert.match(JSON.stringify(entries[0]), /数量 2/);
    const action = await runtime.submitMessage(
      'fixture-action-command',
      '准备虚构盘点'
    );
    assert.equal((await action.wait(context)).status, 'done');
    assert.equal(calls[2].tool, 'business_capabilities');
    assert.deepEqual(calls[3].arguments, {
      operation: 'prepare_count',
      data: { location: 1 }
    });
    assert.equal(calls[3].command_id, calls[4].command_id);
    assert.notEqual(calls[3].step_id, calls[4].step_id);
    assert.equal(effects.size, 1);
    const nextAction = await runtime.submitMessage(
      'fixture-next-action',
      '再次准备相同虚构盘点'
    );
    await nextAction.wait(context);
    assert.notEqual(calls[5].command_id, calls[3].command_id);
    assert.equal(effects.size, 2);
    const loop = await runtime.submitMessage(
      'fixture-loop-command',
      '虚构工具预算验证'
    );
    await loop.wait(context);
    assert.equal(calls.length, 18);
    const notices = (
      await runtime.root.entries({}, 100, undefined, context)
    ).items.filter((entry) => entry.kind === 'cangxu.notice');
    assert.equal(notices.length, 1);
    assert.match(JSON.stringify(notices[0]), /调用上限/);
    const agent = await runtime.root.agent(context);
    assert.deepEqual(agent.tools.map((tool) => tool.name).sort(), [
      'business_action',
      'business_capabilities',
      'business_query',
      'workflow_knowledge'
    ]);
  } finally {
    await runtime.close();
    await new Promise<void>((resolve) => backend.close(() => resolve()));
    await rm(dir, { recursive: true, force: true });
  }
});
