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
      console.error('Failed to load plugin source:', error);
      return null;
    })
    .then((module) => {
      console.log('Loaded external plugin source:', module);
      return module;
    });

  return module;
}
