import { createHash } from 'node:crypto';
import { defineDoc, defineTask } from '@earendil-works/pi-durable';
export type ReceiptWork = {
  grant_id: number;
  grant_version: number;
  receipt_id: string;
  attachments?: { id: number; kind: 'photo' | 'report' }[];
};
export type ReceiptDelivery = {
  key: string;
  source: 'event' | 'timer';
  dueAt: number;
  work: ReceiptWork;
};
export const ReceiptNotices = defineDoc<{
  fingerprints: Record<string, string>;
}>({
  kind: 'cangxu.receipt-notices',
  version: 1,
  scope: 'conversation',
  history: 'latest',
  fork: 'initial',
  initial: () => ({ fingerprints: {} })
});
type Phase = 'intent' | 'link' | 'query' | 'result' | 'failure';
type Checkpoint = {
  [P in Phase]: {
    phase: P;
    index: number;
    status?: string;
    missing?: string[];
    attempts?: number;
    retryAt?: number;
    retryPhase?: 'link' | 'query';
    errorCode?: string;
    permanent?: boolean;
  };
}[Phase];
type GatewayResult = {
  status?: string;
  missing?: string[];
  errorCode?: string;
  permanent?: boolean;
};
const labels: Record<string, string> = {
  inspection: '验收记录',
  inspection_conclusion: '验收结论',
  inspector: '本人检验记录',
  warehouse_signature: '仓管签字',
  purchaser_signature: '采购签字',
  exception_disposition: '异常处置',
  photo: '实物照片',
  report: '验收单',
  signed_acceptance: '验收签字'
};
const digest = (value: unknown) =>
  createHash('sha256').update(JSON.stringify(value)).digest('hex');
export function receiptDuty(
  env: NodeJS.ProcessEnv,
  allowed: (
    tx: import('@earendil-works/pi-durable').Tx,
    conversation: import('@earendil-works/pi-durable').ConversationId,
    taskId: number
  ) => Promise<boolean>
) {
  const call = async (
    input: ReceiptDelivery,
    taskId: number,
    step: string,
    tool: string,
    args: object = {}
  ): Promise<GatewayResult> => {
    try {
      const base = env.ASSISTANT_DJANGO_URL;
      const token = env.ASSISTANT_RUNTIME_TOKEN ?? env.ASSISTANT_INTERNAL_TOKEN;
      if (
        !base ||
        !token ||
        !env.ASSISTANT_DEPLOYMENT_ID ||
        !env.ASSISTANT_PARTNER_ID
      )
        throw new Error('Business gateway configuration missing');
      const response = await fetch(
        new URL('/api/cangxu/assistant/internal/tools/', base),
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Assistant-Deployment': env.ASSISTANT_DEPLOYMENT_ID,
            'Content-Type': 'application/json'
          },
          signal: AbortSignal.timeout(15000),
          body: JSON.stringify({
            partner_id: env.ASSISTANT_PARTNER_ID,
            grant_id: input.work.grant_id,
            grant_version: input.work.grant_version,
            command_id: `receipt:${digest([input.work.grant_id, input.work.grant_version, input.work.receipt_id, step])}`,
            run_id: String(taskId),
            step_id: step,
            tool,
            object_id: input.work.receipt_id,
            args
          })
        }
      );
      if (!response.ok)
        return {
          errorCode: `http_${response.status}`,
          permanent: response.status < 500 && response.status !== 429
        };
      const text = await response.text();
      if (text.length > 65536)
        throw new Error('Business gateway result exceeds limit');
      return JSON.parse(text) as GatewayResult;
    } catch {
      return { errorCode: 'gateway_unreachable', permanent: false };
    }
  };
  return defineTask<ReceiptDelivery, Checkpoint, { business_status: string }>({
    name: 'cangxu.receipt-duty',
    version: 1,
    initial: () => ({ phase: 'intent', index: 0 }),
    phases: {
      intent: async (task, runtime, context) => {
        await runtime.sleep(task.input.dueAt, context);
        await runtime.commit(
          async (tx) =>
            (await allowed(tx, task.conversationId, task.id))
              ? { status: 'running', checkpoint: { phase: 'link', index: 0 } }
              : { status: 'terminal', outcome: { status: 'aborted' } },
          context
        );
      },
      link: async (task, runtime, context) => {
        let permitted = false;
        await runtime.commit(async (tx) => {
          permitted = await allowed(tx, task.conversationId, task.id);
          if (!permitted)
            return { status: 'terminal', outcome: { status: 'aborted' } };
        }, context);
        if (!permitted) return;
        const attachment =
          task.input.work.attachments?.[task.state.checkpoint.index];
        if (attachment) {
          const linked = await call(
            task.input,
            task.id,
            `link:${attachment.id}:${attachment.kind}`,
            'link_receipt_archive',
            { attachment_id: attachment.id, kind: attachment.kind }
          );
          if (linked.errorCode || linked.status !== 'linked') {
            const attempts = (task.state.checkpoint.attempts ?? 0) + 1;
            await runtime.commit(
              () => ({
                status: 'running',
                checkpoint: {
                  ...task.state.checkpoint,
                  phase: 'failure',
                  retryPhase: 'link',
                  attempts,
                  retryAt: Date.now() + 500 * 2 ** (attempts - 1),
                  errorCode: linked.errorCode ?? 'invalid_link_result',
                  permanent: linked.permanent ?? !linked.errorCode
                }
              }),
              context
            );
            return;
          }
        }
        await runtime.commit(
          async (tx) =>
            (await allowed(tx, task.conversationId, task.id))
              ? {
                  status: 'running',
                  checkpoint: attachment
                    ? { phase: 'link', index: task.state.checkpoint.index + 1 }
                    : { phase: 'query', index: task.state.checkpoint.index }
                }
              : { status: 'terminal', outcome: { status: 'aborted' } },
          context
        );
      },
      query: async (task, runtime, context) => {
        let permitted = false;
        await runtime.commit(async (tx) => {
          permitted = await allowed(tx, task.conversationId, task.id);
          if (!permitted)
            return { status: 'terminal', outcome: { status: 'aborted' } };
        }, context);
        if (!permitted) return;

        const result = await call(
          task.input,
          task.id,
          'status',
          'receipt_status'
        );
        if (
          result.errorCode ||
          !['ready', 'waiting'].includes(result.status ?? '')
        ) {
          const attempts = (task.state.checkpoint.attempts ?? 0) + 1;
          await runtime.commit(
            () => ({
              status: 'running',
              checkpoint: {
                ...task.state.checkpoint,
                phase: 'failure',
                retryPhase: 'query',
                attempts,
                retryAt: Date.now() + 500 * 2 ** (attempts - 1),
                errorCode: result.errorCode ?? 'invalid_status_result',
                permanent: result.permanent ?? !result.errorCode
              }
            }),
            context
          );
          return;
        }
        await runtime.commit(
          () => ({
            status: 'running',
            checkpoint: {
              phase: 'result',
              index: task.state.checkpoint.index,
              status: result.status,
              missing: Array.isArray(result.missing)
                ? result.missing
                    .filter((item) => typeof item === 'string')
                    .slice(0, 20)
                : []
            }
          }),
          context
        );
      },
      failure: async (task, runtime, context) => {
        if (
          !task.state.checkpoint.permanent &&
          (task.state.checkpoint.attempts ?? 0) <= 3
        ) {
          await runtime.sleep(
            task.state.checkpoint.retryAt ?? Date.now(),
            context
          );
          await runtime.commit(
            async (tx) =>
              (await allowed(tx, task.conversationId, task.id))
                ? {
                    status: 'running',
                    checkpoint: {
                      ...task.state.checkpoint,
                      phase: task.state.checkpoint.retryPhase ?? 'query'
                    }
                  }
                : { status: 'terminal', outcome: { status: 'aborted' } },
            context
          );
          return;
        }
        await runtime.commit(async (tx) => {
          if (!(await allowed(tx, task.conversationId, task.id)))
            return { status: 'terminal', outcome: { status: 'aborted' } };
          const notices = await tx.doc(ReceiptNotices, task.conversationId);
          const key = `${task.input.work.grant_id}:${task.input.work.receipt_id}`;
          const code = task.state.checkpoint.errorCode ?? 'gateway_failed';
          const fingerprint = digest(['failed', code]);
          if (notices.fingerprints[key] !== fingerprint) {
            await tx.appendEntry(task.conversationId, {
              kind: 'cangxu.notice',
              data: {
                text: '入库归档跟进暂未完成，业务服务未确认本次结果；已保留执行记录，恢复后将按原回执核实。',
                receipt_id: task.input.work.receipt_id,
                status: 'failed'
              }
            });
            notices.fingerprints[key] = fingerprint;
          }
          return {
            status: 'terminal',
            outcome: { status: 'failed', error: { message: code } }
          };
        }, context);
      },
      result: async (task, runtime, context) => {
        await runtime.commit(async (tx) => {
          if (!(await allowed(tx, task.conversationId, task.id)))
            return { status: 'terminal', outcome: { status: 'aborted' } };
          const notices = await tx.doc(ReceiptNotices, task.conversationId);
          const key = `${task.input.work.grant_id}:${task.input.work.receipt_id}`;
          const status = task.state.checkpoint.status ?? 'waiting';
          const waiting = task.state.checkpoint.missing ?? [];
          const fingerprint = digest([status, [...waiting].sort()]);
          if (notices.fingerprints[key] !== fingerprint) {
            await tx.appendEntry(task.conversationId, {
              kind: 'cangxu.notice',
              data: {
                text:
                  status === 'ready'
                    ? '入库归档检查：业务服务确认材料齐备，正式归档状态仍以业务记录为准。'
                    : `入库归档检查：仍待补齐${waiting.length ? `（${waiting.map((key) => labels[key] ?? '业务资料').join('、')}）` : '业务条件'}。`,
                receipt_id: task.input.work.receipt_id,
                status
              }
            });
            notices.fingerprints[key] = fingerprint;
          }
          return {
            status: 'terminal',
            outcome: {
              status: 'completed',
              result: { business_status: status }
            }
          };
        }, context);
      }
    },
    abort: async (_task, runtime, context) => {
      await runtime.commit(
        () => ({ status: 'terminal', outcome: { status: 'aborted' } }),
        context
      );
    }
  });
}
