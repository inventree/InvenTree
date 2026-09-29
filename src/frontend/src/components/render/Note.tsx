import type { ReactNode } from 'react';

import { type InstanceRenderInterface, RenderInlineModel } from './Instance';

export function RenderNoteTemplate({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return (
    instance && (
      <RenderInlineModel
        primary={instance.title}
        suffix={instance.description}
      />
    )
  );
}
