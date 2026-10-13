// Trusted local S0 test protocol. No HTTP listener or business tool is exposed.
import { createInterface } from 'node:readline';
import type { TaskId } from '@earendil-works/pi-durable';
import { context, openRuntime } from './runtime.ts';
const runtime = await openRuntime(
  process.argv[2] ?? '.state/synthetic.sqlite',
  { ...process.env, ASSISTANT_MODEL_PROVIDER: 'fixture' }
);
console.log(JSON.stringify({ ready: true }));
for await (const line of createInterface({ input: process.stdin })) {
  try {
    const command = JSON.parse(line);
    if (command.action === 'deliver')
      console.log(
        JSON.stringify({ task: await runtime.deliver(command.input) })
      );
    else if (command.action === 'snapshot')
      console.log(JSON.stringify(await runtime.snapshot()));
    else if (command.action === 'wait')
      console.log(
        JSON.stringify(
          (await runtime.harness.waitForTask(command.task as TaskId, context))
            .state
        )
      );
    else if (command.action === 'control') {
      await runtime.control(command.key, command.scope, command.task);
      console.log(JSON.stringify({ controlled: true }));
    } else throw new Error('Unknown command');
  } catch (error) {
    console.log(
      JSON.stringify({
        error: error instanceof Error ? error.message : 'Command failed'
      })
    );
  }
}
await runtime.close();
