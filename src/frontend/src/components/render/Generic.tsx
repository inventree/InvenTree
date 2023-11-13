import { ReactNode } from 'react';

import { RenderInlineModel } from './Instance';

export function RenderProjectCode({ instance }: { instance: any }): ReactNode {
  return (
    instance && (
      <RenderInlineModel
        primary={instance.code}
        secondary={instance.description}
      />
    )
  );
}
