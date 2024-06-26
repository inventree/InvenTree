import { ReactNode } from 'react';

import { InstanceRenderInterface, RenderInlineModel } from './Instance';

export function RenderProjectCode({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return (
    instance && (
      <RenderInlineModel
        primary={instance.code}
        secondary={instance.description}
      />
    )
  );
}
