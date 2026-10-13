import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { AssistantEntry } from '@earendil-works/pi-durable';
import { context, openRuntime } from './runtime.ts';
if (process.env.ASSISTANT_MODEL_PROVIDER !== 'openai-compatible')
  throw new Error('Smoke requires an explicitly configured provider');
const dir = await mkdtemp(join(tmpdir(), 'cangxu-model-smoke-'));
const runtime = await openRuntime(join(dir, 'smoke.sqlite'), process.env);
try {
  const submission = await runtime.root.submit(
    {
      type: 'input',
      requestId: 'synthetic-smoke-1',
      content:
        'This is a synthetic connectivity test. Reply exactly CANGXU_OK. Do not call tools.'
    },
    context
  );
  const settled = await submission.wait(context);
  if (settled.status !== 'done' || settled.type !== 'input')
    throw new Error('Provider smoke did not produce a completed answer');
  const answer = await runtime.root.commit(
    (tx) => tx.entry(AssistantEntry, settled.answer),
    context
  );
  const content = answer?.model?.[0];
  if (
    content?.role !== 'assistant' ||
    !content.content.some(
      (block) => block.type === 'text' && block.text.includes('CANGXU_OK')
    )
  )
    throw new Error('Provider returned an unexpected synthetic answer');
  console.log(
    JSON.stringify({
      smoke: 'passed',
      provider: process.env.ASSISTANT_MODEL_PROVIDER,
      model: process.env.ASSISTANT_MODEL_ID,
      persistedAnswer: settled.answer
    })
  );
} finally {
  await runtime.close();
  await rm(dir, { recursive: true, force: true });
}
