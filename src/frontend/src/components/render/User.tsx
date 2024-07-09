import { IconUser, IconUsersGroup } from '@tabler/icons-react';
import { ReactNode } from 'react';

import { InstanceRenderInterface, RenderInlineModel } from './Instance';

export function RenderOwner({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return (
    instance && (
      <RenderInlineModel
        primary={instance.name}
        suffix={instance.label == 'group' ? <IconUsersGroup /> : <IconUser />}
      />
    )
  );
}

export function RenderUser({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return (
    instance && (
      <RenderInlineModel
        primary={instance.username}
        secondary={`${instance.first_name} ${instance.last_name}`}
      />
    )
  );
}
