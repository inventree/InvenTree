import { useLocalState } from '../../states/LocalState';

/*
 * Load an external plugin source from a URL.
 */
export async function loadExternalPluginSource(source: string) {
  const host = useLocalState.getState().host;

  source = source.trim();

  // If no source is provided, clear the plugin content
  if (!source) {
    return null;
  }

  // If the source is a relative URL, prefix it with the host URL
  if (source.startsWith('/')) {
    source = `${host}${source}`;
  }

  const module = await import(/* @vite-ignore */ source)
    .catch((error) => {
      console.error(`ERR: Failed to load plugin from ${source}:`, error);
      return null;
    })
    .then((module) => {
      return module;
    });

  return module;
}

/*
 * Find a named function in an external plugin source.
 */
export async function findExternalPluginFunction(
  source: string,
  functionName: string
): Promise<Function | null> {
  // The source URL may also include the function name divided by a colon
  // otherwise the provided function name will be used
  if (source.includes(':')) {
    [source, functionName] = source.split(':');
  }

  const module = await loadExternalPluginSource(source);

  if (module && module[functionName]) {
    return module[functionName];
  }

  return null;
}
