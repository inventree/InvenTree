import { IconUser, IconUsersGroup } from '@tabler/icons-react';
import type { ReactNode } from 'react';

import { type InstanceRenderInterface, RenderInlineModel } from './Instance';

export function RenderOwner({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return (
    instance && (
      <RenderInlineModel
        primary={instance.name}
        suffix={
          instance.label == 'group' ? (
            <IconUsersGroup size={16} />
          ) : (
            <IconUser size={16} />
          )
        }
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

export function RenderGroup({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return instance && <RenderInlineModel primary={instance.name} />;
}
