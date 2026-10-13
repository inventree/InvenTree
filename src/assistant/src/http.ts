import { createHash, timingSafeEqual } from 'node:crypto';
import { mkdir, readdir } from 'node:fs/promises';
import { type IncomingMessage, createServer } from 'node:http';
import { join, resolve } from 'node:path';
import type { EntryId, TaskId } from '@earendil-works/pi-durable';
import { attachmentMetadata } from './attachments.ts';
import type { ReceiptWork } from './receipt-duty.ts';
import { businessReferences, context, openRuntime } from './runtime.ts';
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
class ProtocolError extends Error {
  readonly status: number;
  readonly code: string;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}
async function body(request: IncomingMessage) {
  if (!(request.headers['content-type'] ?? '').startsWith('application/json'))
    throw new ProtocolError(400, 'invalid_request', 'JSON body required');
  const chunks: Buffer[] = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > 65536)
      throw new ProtocolError(
        413,
        'body_too_large',
        'Request body exceeds limit'
      );
    chunks.push(chunk);
  }
  try {
    const result = JSON.parse(Buffer.concat(chunks).toString('utf8'));
    if (!result || typeof result !== 'object' || Array.isArray(result))
      throw new Error();
    return result as Record<string, unknown>;
  } catch {
    throw new ProtocolError(400, 'invalid_request', 'Invalid JSON object');
  }
}
export async function createRuntimeServer(env: NodeJS.ProcessEnv) {
  const token = env.ASSISTANT_RUNTIME_TOKEN ?? env.ASSISTANT_INTERNAL_TOKEN;
  const deployment = env.ASSISTANT_DEPLOYMENT_ID;
  if (!token || token.length < 32 || !deployment || !UUID.test(deployment))
    throw new Error('Internal token (32+ chars) and deployment UUID required');
  const maxPartners = Number(env.ASSISTANT_MAX_PARTNERS ?? 32);
  if (
    !Number.isSafeInteger(maxPartners) ||
    maxPartners < 1 ||
    maxPartners > 128
  )
    throw new Error('Invalid runtime pool limit');
  const directory = join(
    resolve(env.ASSISTANT_STORAGE_DIR ?? '.state'),
    deployment
  );
  await mkdir(directory, { recursive: true, mode: 0o700 });
  const pool = new Map<
    string,
    Promise<Awaited<ReturnType<typeof openRuntime>>>
  >();
  async function runtime(partner: string) {
    if (!UUID.test(partner))
      throw new ProtocolError(400, 'invalid_partner', 'Partner UUID required');
    let result = pool.get(partner);
    if (!result) {
      if (pool.size >= maxPartners)
        throw new ProtocolError(
          503,
          'capacity',
          'Runtime partner capacity reached'
        );
      result = openRuntime(join(directory, `${partner}.sqlite`), {
        ...env,
        ASSISTANT_PARTNER_ID: partner
      });
      pool.set(partner, result);
      result.catch(() => pool.delete(partner));
    }
    return result;
  }
  const files = (await readdir(directory)).filter(
    (name) => name.endsWith('.sqlite') && UUID.test(name.slice(0, -7))
  );
  if (files.length > maxPartners)
    throw new Error('Known storages exceed configured runtime capacity');
  try {
    for (const name of files) await runtime(name.slice(0, -7));
  } catch (error) {
    await Promise.allSettled(
      [...pool.values()].map(async (item) => (await item).close())
    );
    throw error;
  }
  const digest = (value: string) => createHash('sha256').update(value).digest();
  const expected = digest(`Bearer ${token}`);
  const server = createServer(async (request, response) => {
    response.setHeader('Content-Type', 'application/json; charset=utf-8');
    response.setHeader('Cache-Control', 'no-store');
    try {
      if (
        !timingSafeEqual(digest(request.headers.authorization ?? ''), expected)
      )
        throw new ProtocolError(
          401,
          'unauthorized',
          'Internal authentication required'
        );
      if (request.headers['x-assistant-deployment'] !== deployment)
        throw new ProtocolError(
          403,
          'deployment_mismatch',
          'Deployment header does not match runtime'
        );
      const url = new URL(request.url ?? '/', 'http://localhost');
      const match =
        /^\/v1\/partners\/([^/]+)(?:\/(messages|events|controls|status))?$/.exec(
          url.pathname
        );
      if (!match)
        throw new ProtocolError(404, 'not_found', 'Unknown runtime route');
      const partner = match[1];
      const route = match[2];
      const active = await runtime(partner);
      let result: unknown;
      if (request.method === 'GET' && (!route || route === 'status')) {
        const inspect = await active.harness.inspect(context);
        const ledger = await active.snapshot();
        const recentTasks = await Promise.all(
          Object.values(ledger?.deliveries ?? {})
            .slice(-20)
            .map(async (delivery) => {
              const task = await active.harness.getTask(
                delivery.task as TaskId,
                context
              );
              return {
                id: delivery.task,
                status:
                  task?.state.status === 'terminal'
                    ? task.state.outcome.status
                    : (task?.state.status ?? 'unknown')
              };
            })
        );
        const view = await active.root.viewState(context);
        let liveMessage: { id: string; role: string; text: string } | null =
          null;
        let liveTools: { id: unknown; name: unknown; status: unknown }[] = [];
        try {
          const live = view.value.docs['pi.live'] as
            | {
                run?: { taskId?: number };
                generation?: {
                  message?: { content?: { type: string; text?: string }[] };
                };
                tools?: { callId: string; name: string; status: string }[];
              }
            | undefined;
          const partial =
            live?.generation?.message?.content
              ?.filter((part) => part.type === 'text')
              .map((part) => part.text ?? '')
              .join('') ?? '';
          if (partial && live?.run)
            liveMessage = {
              id: `live:${live.run.taskId}`,
              role: 'assistant',
              text: partial
            };
          liveTools = (live?.tools ?? []).map((tool) => ({
            id: tool.callId,
            name: tool.name,
            status: tool.status
          }));
        } finally {
          view.dispose();
        }
        const deliveries = await Promise.all(
          Object.keys(ledger?.messageHashes ?? {})
            .slice(-50)
            .map(async (requestId) => {
              const item = await active.root.commit(
                (tx) => tx.submissionByRequest(active.root.id, requestId),
                context
              );
              return {
                client_request_id: requestId,
                request_id: requestId,
                status: item?.status ?? 'pending',
                ...(item?.status === 'unanswered'
                  ? { reason: item.reason }
                  : {})
              };
            })
        );
        result = {
          deliveries,
          live_message: liveMessage,
          live_tools: liveTools,
          recent_tasks: recentTasks,
          partner_id: partner,
          status: inspect.submissions.length ? 'processing' : 'available',
          is_running: inspect.submissions.length > 0,
          reply_running: inspect.submissions.length > 0,
          scheduling: inspect.scheduling,
          active_tasks: inspect.tasks.map((task) => ({
            id: task.record.id,
            kind: task.record.kind,
            status: task.state.kind,
            background: task.record.background ?? false
          })),
          submissions: inspect.submissions.map((item) => ({
            id: item.id,
            request_id: item.requestId,
            status: item.status
          })),
          background_stopped: ledger?.stopped ?? false,
          pending_tasks: inspect.tasks.length,
          capabilities: {
            images: env.ASSISTANT_MODEL_SUPPORTS_IMAGES !== 'false',
            attachment_upload: true,
            file_context: true
          },
          protocol_version: 1
        };
      } else if (request.method === 'GET' && route === 'messages') {
        const limit = Number(url.searchParams.get('limit') ?? 50);
        const before = url.searchParams.get('before');
        if (
          !Number.isInteger(limit) ||
          limit < 1 ||
          limit > 100 ||
          (before !== null && (!/^\d+$/.test(before) || Number(before) < 1))
        )
          throw new ProtocolError(
            400,
            'invalid_request',
            'Invalid history bounds'
          );
        const entries = await active.root.entries(
          before ? { maxEntryId: (Number(before) - 1) as EntryId } : {},
          Math.min(limit * 4, 400),
          undefined,
          context
        );
        const items = entries.items
          .flatMap<Record<string, unknown> & { id: number }>((entry) => {
            if (
              entry.kind === 'cangxu.notice' &&
              entry.data &&
              typeof entry.data === 'object' &&
              'text' in entry.data &&
              typeof entry.data.text === 'string'
            )
              return [
                {
                  id: entry.id,
                  role: 'assistant' as const,
                  text: entry.data.text
                }
              ];
            if (
              entry.kind === 'cangxu.user' &&
              entry.data &&
              typeof entry.data === 'object' &&
              !Array.isArray(entry.data)
            ) {
              const data = entry.data;
              return [
                {
                  id: entry.id,
                  role: 'user' as const,
                  text: String(data.text ?? ''),
                  content: [{ type: 'text', text: String(data.text ?? '') }],
                  request_id: data.request_id,
                  client_request_id: data.request_id,
                  attachments: data.attachments ?? [],
                  references: data.references ?? [],
                  created_at: data.created_at
                }
              ];
            }
            if (!['pi.user', 'pi.assistant'].includes(entry.kind)) return [];
            return (entry.model ?? []).flatMap((message) => {
              if (message.role !== 'user' && message.role !== 'assistant')
                return [];
              let text =
                typeof message.content === 'string'
                  ? message.content
                  : message.content
                      .filter((block) => block.type === 'text')
                      .map((block) => block.text)
                      .join('');
              if (
                message.role === 'assistant' &&
                message.stopReason === 'error'
              ) {
                const reason = /timed?\s*out|timeout/i.test(
                  message.errorMessage ?? ''
                )
                  ? '模型服务请求超时'
                  : '模型服务发生异常';
                text = `${text ? `${text}\n\n` : ''}${reason}，本次回复未完成。你的消息已保留，可补充消息继续；已执行的业务结果请先核实。`;
              }
              return text
                ? [
                    {
                      id: entry.id,
                      role: message.role,
                      text,
                      content: [{ type: 'text', text }],
                      attachments: [],
                      created_at: new Date(message.timestamp).toISOString()
                    }
                  ]
                : [];
            });
          })
          .slice(0, limit);
        result = {
          items: [...items].reverse(),
          next_before: items.at(-1)?.id ?? entries.items.at(-1)?.id ?? null,
          has_more:
            entries.items.length >= Math.min(limit * 4, 400) ||
            items.length >= limit
        };
      } else if (request.method === 'POST' && route === 'messages') {
        const input = await body(request);
        let attachments: ReturnType<typeof attachmentMetadata>;
        let references: ReturnType<typeof businessReferences>;
        try {
          attachments = attachmentMetadata(input.attachments);
          references = businessReferences(input.references);
        } catch {
          throw new ProtocolError(
            400,
            'invalid_request',
            'Invalid attachments or references'
          );
        }
        if (
          typeof input.request_id !== 'string' ||
          typeof input.text !== 'string' ||
          (!input.text.trim() && !attachments.length && !references.length) ||
          input.text.length > 16000 ||
          !input.request_id ||
          input.request_id.length > 200
        )
          throw new ProtocolError(
            400,
            'invalid_request',
            'Valid request_id and text required'
          );
        const submission = await active.submitMessage(
          input.request_id,
          input.text,
          attachments,
          references
        );
        result = { submission_id: submission.id, status: 'accepted' };
        response.statusCode = 202;
      } else if (request.method === 'POST' && route === 'events') {
        const input = await body(request);
        if (
          typeof input.key !== 'string' ||
          !input.key ||
          input.key.length > 200 ||
          !['event', 'timer'].includes(String(input.source)) ||
          !Number.isSafeInteger(input.dueAt)
        )
          throw new ProtocolError(
            400,
            'invalid_request',
            'Invalid event delivery'
          );
        const work = input.work as ReceiptWork | undefined;
        if (
          work &&
          (!Number.isSafeInteger(work.grant_id) ||
            work.grant_id < 1 ||
            !Number.isSafeInteger(work.grant_version) ||
            work.grant_version < 1 ||
            typeof work.receipt_id !== 'string' ||
            !work.receipt_id ||
            work.receipt_id.length > 200 ||
            (work.attachments !== undefined &&
              (!Array.isArray(work.attachments) ||
                work.attachments.length > 20 ||
                work.attachments.some(
                  (a) =>
                    !Number.isSafeInteger(a.id) ||
                    a.id < 1 ||
                    !['photo', 'report'].includes(a.kind)
                ))))
        )
          throw new ProtocolError(
            400,
            'invalid_request',
            'Invalid pinned receipt work'
          );
        result = {
          task_id: await active.deliver({
            key: input.key,
            source: input.source as 'event' | 'timer',
            dueAt: input.dueAt as number,
            ...(work ? { work } : {})
          }),
          status: 'accepted',
          execution: work ? 'receipt_check_pending' : 'synthetic_check_only'
        };
        response.statusCode = 202;
      } else if (request.method === 'POST' && route === 'controls') {
        const input = await body(request);
        input.key ??= input.request_id;
        input.task ??= input.task_id;
        if (
          typeof input.key !== 'string' ||
          !input.key ||
          input.key.length > 200 ||
          (input.scope === 'task' && input.task === undefined) ||
          !['reply', 'task', 'all-background', 'all-writes'].includes(
            String(input.scope)
          ) ||
          (input.task !== undefined && !Number.isSafeInteger(input.task))
        )
          throw new ProtocolError(400, 'invalid_request', 'Invalid control');
        await active.control(
          input.key,
          input.scope as 'reply' | 'task' | 'all-background' | 'all-writes',
          input.task as TaskId | undefined
        );
        result = { status: 'controlled' };
      } else
        throw new ProtocolError(
          405,
          'method_not_allowed',
          'Unsupported runtime operation'
        );
      response.end(JSON.stringify(result));
    } catch (error) {
      const conflict =
        error instanceof Error &&
        /reused|persistently stopped/.test(error.message);
      response.statusCode =
        error instanceof ProtocolError ? error.status : conflict ? 409 : 503;
      response.end(
        JSON.stringify({
          error: {
            code:
              error instanceof ProtocolError
                ? error.code
                : conflict
                  ? 'conflict'
                  : 'unavailable',
            message:
              error instanceof ProtocolError
                ? error.message
                : conflict
                  ? 'Request conflicts with durable state'
                  : 'Assistant runtime unavailable'
          }
        })
      );
    }
  });
  server.requestTimeout = 10000;
  server.headersTimeout = 5000;
  server.maxHeadersCount = 30;
  return {
    server,
    async close() {
      if (server.listening)
        await new Promise<void>((resolveClose) =>
          server.close(() => resolveClose())
        );
      await Promise.allSettled(
        [...pool.values()].map(async (item) => (await item).close())
      );
    }
  };
}
