import { ReactNode } from 'react';

import { RenderInlineModel } from './Instance';

export function RenderOwner({ owner }: { owner: any }): ReactNode {
  // TODO: Icon based on user / group status?

  return <RenderInlineModel primary={owner.name} />;
}

export function RenderUser({ user }: { user: any }): ReactNode {
  return (
    <RenderInlineModel
      primary={user.username}
      secondary={`${user.first_name} ${user.last_name}`}
    />
  );
}
