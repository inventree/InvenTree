import { createRuntimeServer } from './http.ts';
const port = Number(process.env.ASSISTANT_PORT ?? 8789);
if (!Number.isInteger(port) || port < 1 || port > 65535)
  throw new Error('Invalid runtime port');
const runtime = await createRuntimeServer(process.env);
runtime.server.listen(port, '127.0.0.1', () =>
  console.log(JSON.stringify({ ready: true, protocol_version: 1, port }))
);
for (const signal of ['SIGINT', 'SIGTERM'] as const)
  process.once(signal, async () => {
    await runtime.close();
    process.exit(0);
  });
