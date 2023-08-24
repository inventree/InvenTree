import { Anchor, Group, Text } from '@mantine/core';
import { IconUser } from '@tabler/icons-react';

import { ApiPaths, url } from '../../states/ApiState';

export function UserRenderer({ detail, user }: { detail: any; user?: any }) {
  if (detail)
    return (
      <Anchor href={url(ApiPaths.frontend_user, detail.pk)}>
        <Group spacing={0}>
          <IconUser size={16} />
          <Text>{detail.username}</Text>
        </Group>
      </Anchor>
    );
  return (
    <Group spacing={0}>
      <IconUser size={16} />
      <Text>{user}</Text>
    </Group>
  );
}
