import { t } from '@lingui/core/macro';

export const NoteContentTypes = {
  html: 'text/html',
  json: 'application/json',
  plainText: 'text/plain'
} as const;

export type NoteContentType =
  (typeof NoteContentTypes)[keyof typeof NoteContentTypes];

/** Return editor settings for a supported note content type. */
export function noteContentHandler(contentType: NoteContentType) {
  const handlers = {
    [NoteContentTypes.html]: { label: t`HTML`, raw: false, initialContent: '' },
    [NoteContentTypes.json]: {
      label: t`JSON`,
      raw: true,
      initialContent: '{}'
    },
    [NoteContentTypes.plainText]: {
      label: t`Plain text`,
      raw: true,
      initialContent: ''
    }
  };
  const handler = handlers[contentType];
  if (!handler) {
    throw new Error(`Unsupported note content type: ${contentType}`);
  }
  return handler;
}
