import type { ReactNode } from 'react';

import { RenderInlineModel } from './Instance';

export function RenderNoteTemplate({
  instance
}: Readonly<{
  instance: any;
}>): ReactNode {
  return (
    <RenderInlineModel primary={instance.title} suffix={instance.description} />
  );
}
