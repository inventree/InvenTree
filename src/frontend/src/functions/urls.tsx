import { useLocalState } from '../../lib/states/LocalState';

/**
 * Returns the edit view URL for a given model type
 */
export function generateUrl(url: string | URL, base?: string): string {
  const { host } = useLocalState.getState();

  let newUrl: string | URL = url;

  try {
    if (base) {
      newUrl = new URL(url, base).toString();
    } else if (host) {
      newUrl = new URL(url, host).toString();
    } else {
      newUrl = url.toString();
    }
  } catch (e: any) {
    console.error(`ERR: generateURL failed. url='${url}', base='${base}'`);
  }

  return newUrl.toString();
}
