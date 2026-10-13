import { createHash } from 'node:crypto';
import { mkdir, realpath } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { BACKGROUND_CONTEXT as context } from '@earendil-works/chord/context';
import type { FauxResponseStep } from '@earendil-works/pi-ai/providers/faux';
import {
  Harness,
  type TaskId,
  createRegistry,
  defineDoc,
  defineExtension,
  defineTask
} from '@earendil-works/pi-durable';
import { openNodeSqliteStorage } from '@earendil-works/pi-durable/storage/sqlite/node';
import {
  type AttachmentMetadata,
  attachmentInput,
  attachmentMetadata
} from './attachments.ts';
import { modelTools } from './model-tools.ts';
import { configuredModels } from './provider.ts';
import { type ReceiptDelivery, receiptDuty } from './receipt-duty.ts';

export { context };
export type BusinessReference = {
  object_type: string;
  object_id: string;
  label: string;
  page_url: string;
};
export function businessReferences(input: unknown): BusinessReference[] {
  if (input === undefined) return [];
  if (!Array.isArray(input) || input.length > 8)
    throw new Error('Invalid references');
  const types = [
    'part',
    'stock',
    'location',
    'purchase_order',
    'build',
    'sales_order',
    'shipment',
    'configuration',
    'purchase_receipt'
  ];
  return input.map((item) => {
    if (
      !item ||
      !types.includes(item.object_type) ||
      !/^\d{1,15}$/.test(String(item.object_id)) ||
      Number(item.object_id) < 1 ||
      typeof item.label !== 'string' ||
      item.label.length > 300 ||
      typeof item.page_url !== 'string' ||
      item.page_url.length > 500 ||
      !item.page_url.startsWith('/') ||
      item.page_url.startsWith('//') ||
      /[\\\r\n]/.test(item.page_url)
    )
      throw new Error('Invalid references');
    return {
      object_type: item.object_type,
      object_id: String(item.object_id),
      label: item.label,
      page_url: item.page_url
    };
  });
}
type Delivery = { key: string; source: 'event' | 'timer'; dueAt: number };
type LedgerState = {
  deliveries: Record<string, { hash: string; task: number }>;
  completed: string[];
  stopped: boolean;
  stoppedTasks: number[];
  controls: Record<string, string>;
  messageHashes?: Record<string, string>;
};
const Ledger = defineDoc<LedgerState>({
  kind: 'cangxu.s0.ledger',
  version: 1,
  scope: 'conversation',
  history: 'latest',
  fork: 'initial',
  initial: () => ({
    deliveries: {},
    completed: [],
    stopped: false,
    stoppedTasks: [],
    controls: {}
  })
});
const SyntheticCheck = defineTask<
  Delivery,
  { phase: 'wait'; at: number },
  { key: string }
>({
  name: 'cangxu.s0.synthetic-check',
  version: 1,
  initial: (input) => ({ phase: 'wait', at: input.dueAt }),
  phases: {
    wait: async (task, runtime, taskContext) => {
      await runtime.sleep(task.state.checkpoint.at, taskContext);
      await runtime.commit(async (tx) => {
        const ledger = await tx.doc(Ledger, task.conversationId);
        if (ledger.stopped || ledger.stoppedTasks.includes(task.id))
          return { status: 'terminal', outcome: { status: 'aborted' } };
        if (!ledger.completed.includes(task.input.key))
          ledger.completed.push(task.input.key);
        return {
          status: 'terminal',
          outcome: { status: 'completed', result: { key: task.input.key } }
        };
      }, taskContext);
    }
  },
  abort: async (_task, runtime, taskContext) => {
    await runtime.commit(
      () => ({ status: 'terminal', outcome: { status: 'aborted' } }),
      taskContext
    );
  }
});
const hash = (value: unknown) =>
  createHash('sha256').update(JSON.stringify(value)).digest('hex');

/** A single host process owns each SQLite store, including during SIGKILL recovery.
 * The OS releases this separate exclusive SQLite transaction on process death.
 * Never unlink the ownership file: that could create two lock domains.
 */
export async function openRuntime(
  file: string,
  env: NodeJS.ProcessEnv = {},
  options: { fixtureResponses?: FauxResponseStep[] } = {}
) {
  file = resolve(file);
  await mkdir(dirname(file), { recursive: true, mode: 0o700 });
  try {
    file = await realpath(file);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
    file = resolve(await realpath(dirname(file)), file.split('/').at(-1)!);
  }
  const lock = new DatabaseSync(`${file}.owner.sqlite`);
  try {
    lock.exec('PRAGMA journal_mode=DELETE; BEGIN EXCLUSIVE');
  } catch {
    lock.close();
    throw new Error('Assistant storage already has an owner');
  }
  let harness: Harness | undefined;
  try {
    const { models, model } = configuredModels(env, options.fixtureResponses);
    const ReceiptDuty = receiptDuty(env, async (tx, conversation, taskId) => {
      const ledger = await tx.doc(Ledger, conversation);
      return !ledger.stopped && !ledger.stoppedTasks.includes(taskId);
    });
    const registry = createRegistry();
    const businessTools = modelTools(env);
    if (businessTools) registry.install(businessTools);
    registry.install(
      defineExtension({
        name: 'cangxu-s0',
        tasks: [SyntheticCheck, ReceiptDuty]
      })
    );
    harness = await Harness.open(
      await openNodeSqliteStorage(file),
      {
        models,
        registry,
        settings: {
          stream: { timeoutMs: 30000, maxRetries: 0 },
          retry: { enabled: false, maxRetries: 0, baseDelayMs: 1000 }
        }
      },
      context
    );
    const activeHarness = harness;
    const root = await activeHarness.root(context, { agent: { model: model } });
    // Apply host-selected model to existing idle conversations. A pending Pi
    // generation/tool/compaction keeps its persisted model choice during recovery.
    const pendingPi = (await activeHarness.inspect(context)).tasks.some(
      (task) => task.record.kind.startsWith('pi.')
    );
    if (!pendingPi) await root.configure({ model }, context);
    activeHarness.resume();
    return {
      harness: activeHarness,
      root,
      snapshot: () => activeHarness.snapshot(Ledger, root.id, context),
      async submitMessage(
        requestId: string,
        text: string,
        inputAttachments: AttachmentMetadata[] = [],
        inputReferences: BusinessReference[] = []
      ) {
        const attachments = attachmentMetadata(inputAttachments);
        const references = businessReferences(inputReferences);
        if (
          !requestId ||
          requestId.length > 200 ||
          (!text.trim() && !attachments.length && !references.length) ||
          text.length > 16000
        )
          throw new Error('Invalid message');
        await root.commit(async (tx) => {
          const ledger = await tx.doc(Ledger, root.id);
          ledger.messageHashes ??= {};
          const digest = hash({ text, attachments, references });
          if (
            ledger.messageHashes[requestId] &&
            ledger.messageHashes[requestId] !== digest &&
            !(
              attachments.length === 0 &&
              references.length === 0 &&
              ledger.messageHashes[requestId] === hash(text)
            )
          )
            throw new Error('Message key reused with different content');
          ledger.messageHashes[requestId] = digest;
        }, context);
        const refContext = references.length
          ? `\n业务引用（仅为交办上下文，业务事实须通过工具回查）：${JSON.stringify(references)}`
          : '';
        const prepared = await attachmentInput(
          text + refContext,
          attachments,
          env
        );
        return root.submit(
          {
            type: 'input',
            content: prepared.content,
            requestId,
            entry: {
              kind: 'cangxu.user',
              data: {
                text,
                request_id: requestId,
                attachments: prepared.attachments,
                references,
                created_at: new Date().toISOString()
              }
            }
          },
          context
        );
      },
      async deliver(input: Delivery | ReceiptDelivery) {
        if (
          !input.key ||
          input.key.length > 200 ||
          !Number.isSafeInteger(input.dueAt) ||
          !['event', 'timer'].includes(input.source)
        )
          throw new Error('Invalid synthetic delivery');
        const id = await root.commit(async (tx) => {
          const ledger = await tx.doc(Ledger, root.id);
          const existing = ledger.deliveries[input.key];
          if (existing) {
            if (existing.hash !== hash(input))
              throw new Error('Delivery key reused with different content');
            return existing.task as TaskId<{ key: string }>;
          }
          if (ledger.stopped)
            throw new Error('Background work is persistently stopped');
          const options = {
            ownership: { kind: 'conversation' as const },
            background: true
          };
          const task =
            'work' in input
              ? await tx.createTask(ReceiptDuty, input, options)
              : await tx.createTask(SyntheticCheck, input, options);
          ledger.deliveries[input.key] = { hash: hash(input), task };
          return task;
        }, context);
        activeHarness.resume();
        return id as TaskId;
      },
      async control(
        key: string,
        scope: 'reply' | 'task' | 'all-background' | 'all-writes',
        task?: TaskId
      ) {
        if (
          !key ||
          !['reply', 'task', 'all-background', 'all-writes'].includes(scope) ||
          (scope === 'task' && !task)
        )
          throw new Error('Invalid control');
        await root.commit(async (tx) => {
          const ledger = await tx.doc(Ledger, root.id);
          const digest = hash({ scope, task });
          if (ledger.controls[key] && ledger.controls[key] !== digest)
            throw new Error('Control key reused');
          ledger.controls[key] = digest;
          if (scope === 'all-background') ledger.stopped = true;
          if (scope === 'task' && !ledger.stoppedTasks.includes(task!))
            ledger.stoppedTasks.push(task!);
        }, context);
        if (scope === 'all-writes') return; // Django persists and enforces write qualification.
        // Retrying a recorded control reissues the abort, covering a crash between commits.
        if (scope === 'reply') await root.abort(context);
        else if (scope === 'task')
          await activeHarness.abortTask(task!, context);
        else await root.abort(context, { background: true });
      },
      async close() {
        try {
          await activeHarness.close(context);
        } finally {
          lock.close();
        }
      }
    };
  } catch (error) {
    try {
      await harness?.close(context);
    } finally {
      lock.close();
    }
    throw error;
  }
}
