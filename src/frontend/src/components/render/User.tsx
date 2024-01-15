import { IconUser, IconUsersGroup } from '@tabler/icons-react';
import { ReactNode } from 'react';

import { RenderInlineModel } from './Instance';

export function RenderOwner({ instance }: { instance: any }): ReactNode {
  return (
    instance && (
      <RenderInlineModel
        primary={instance.name}
        suffix={instance.label == 'group' ? <IconUsersGroup /> : <IconUser />}
      />
    )
  );
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
