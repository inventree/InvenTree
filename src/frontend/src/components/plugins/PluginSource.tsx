import { generateUrl } from '../../functions/urls';
import { useLocalState } from '../../states/LocalState';

/*
 * Load an external plugin source from a URL.
 */
export async function loadExternalPluginSource(source: string) {
  source = source.trim();

  // If no source is provided, clear the plugin content
  if (!source) {
    return null;
  }

  const url = generateUrl(source);

  const module = await import(/* @vite-ignore */ url)
    .catch((error) => {
      console.error(`ERR: Failed to load plugin from ${url}:`, error);
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
  const { getHost } = useLocalState.getState();

  // Extract pathstring from the source URL
  // Use the specified host unless the source is already a full URL
  const url = new URL(source, getHost());

  // If the pathname contains a ':' character, it indicates a function name
  // but we need to remove it for the URL lookup to work correctly
  if (url.pathname.includes(':')) {
    const parts = url.pathname.split(':');
    source = parts[0]; // Use the first part as the source URL
    functionName = parts[1] || functionName; // Use the second part as the
    url.pathname = source; // Update the pathname to the source URL
  }

  const module = await loadExternalPluginSource(url.toString());

  if (module?.[functionName]) {
    return module[functionName];
  }

  return null;
}
