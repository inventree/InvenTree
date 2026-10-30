import { useLocalState } from '../states/LocalState';

/**
 * Returns the edit view URL for a given model type
 */
export function generateUrl(url: string | URL, base?: string): string {
  const { getHost } = useLocalState.getState();

  let newUrl: string | URL = url;

  const host: string = getHost();

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

/**
 * Return the file name part of a file URL or storage path.
 * Storage backends such as S3 return presigned URLs, so any query string or fragment is dropped before taking the last path segment.
 */
export function fileNameFromUrl(url?: string | null): string {
  if (!url) {
    return '';
  }

  return url.split('?')[0].split('#')[0].split('/').pop() ?? '';
}
