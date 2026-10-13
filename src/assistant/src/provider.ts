import {
  stream,
  streamSimple
} from '@earendil-works/pi-ai/api/openai-completions';
import { createModels, createProvider } from '@earendil-works/pi-ai/models';
import {
  type FauxResponseStep,
  fauxAssistantMessage,
  fauxProvider
} from '@earendil-works/pi-ai/providers/faux';

/** Credential stays inside provider auth, never in persisted agent/model metadata. */
export function configuredModels(
  env: NodeJS.ProcessEnv = {},
  fixtureResponses?: FauxResponseStep[]
) {
  const models = createModels();
  const kind = env.ASSISTANT_MODEL_PROVIDER ?? 'fixture';
  if (kind === 'fixture') {
    const faux = fauxProvider();
    models.setProvider(faux.provider);
    faux.setResponses(
      fixtureResponses ??
        Array.from({ length: 32 }, () =>
          fauxAssistantMessage('Synthetic assistant acknowledgement.')
        )
    );
    return { models, model: { provider: 'faux', modelId: 'faux-1' } };
  }
  if (kind !== 'openai-compatible')
    throw new Error('Unsupported assistant model provider');
  const baseUrl = env.ASSISTANT_MODEL_BASE_URL;
  const modelId = env.ASSISTANT_MODEL_ID;
  const apiKey = env.ASSISTANT_MODEL_API_KEY;
  if (!baseUrl || !modelId || !apiKey)
    throw new Error('Assistant provider configuration is incomplete');
  const maxTokens = Number(env.ASSISTANT_MODEL_MAX_OUTPUT_TOKENS ?? 256);
  if (!Number.isSafeInteger(maxTokens) || maxTokens < 1)
    throw new Error('Model output token limit must be a positive integer');
  const url = new URL(baseUrl);
  if (
    !['http:', 'https:'].includes(url.protocol) ||
    url.username ||
    url.password
  )
    throw new Error('Invalid provider base URL');
  models.setProvider(
    createProvider({
      id: 'cangxu-compatible',
      baseUrl,
      auth: {
        apiKey: {
          name: 'Configured service credential',
          resolve: async () => ({ auth: { apiKey } })
        }
      },
      models: [
        {
          id: modelId,
          name: modelId,
          provider: 'cangxu-compatible',
          api: 'openai-completions',
          baseUrl,
          reasoning: false,
          input:
            env.ASSISTANT_MODEL_SUPPORTS_IMAGES === 'false'
              ? ['text']
              : ['text', 'image'],
          cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
          contextWindow: 32768,
          maxTokens: Math.min(maxTokens, 8192),
          compat: { supportsDeveloperRole: false, supportsStore: false }
        }
      ],
      api: { stream, streamSimple }
    })
  );
  return { models, model: { provider: 'cangxu-compatible', modelId } };
}
