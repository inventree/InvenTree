import { Badge, Group, Text } from '@mantine/core';
import { IconUser, IconUsersGroup } from '@tabler/icons-react';
import type { ReactNode } from 'react';

import { t } from '@lingui/core/macro';
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
        secondary={
          <Group gap='xs'>
            {instance.is_active === false && (
              <Badge autoContrast color='red'>{t`Inactive`}</Badge>
            )}
          </Group>
        }
        suffix={
          <Group gap='xs'>
            <Text size='sm'>
              {instance.first_name} {instance.last_name}
            </Text>
            <IconUser size={16} />
          </Group>
        }
      />
    )
  );
}

export function RenderGroup({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return instance && <RenderInlineModel primary={instance.name} />;
}
