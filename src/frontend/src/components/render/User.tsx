import { ReactNode } from 'react';

import { RenderInlineModel } from './Instance';

export function RenderOwner({ instance }: { instance: any }): ReactNode {
  // TODO: Icon based on user / group status?

  return instance && <RenderInlineModel primary={instance.name} />;
}

export function RenderUser({ instance }: { instance: any }): ReactNode {
  return (
    instance && (
      <RenderInlineModel
        primary={instance.username}
        secondary={`${instance.first_name} ${instance.last_name}`}
      />
    )
  );
}
