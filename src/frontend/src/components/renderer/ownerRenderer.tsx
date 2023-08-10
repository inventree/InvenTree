import { t } from '@lingui/macro';
import { Anchor, Group, Text, Tooltip } from '@mantine/core';
import { IconUser, IconUsersGroup } from '@tabler/icons-react';

export function ownerRenderer(record: any) {
  return record ? (
    <Tooltip label={record.label} position="bottom">
      <Group spacing={0}>
        {record.label == t`group` ? (
          <IconUsersGroup size={12} />
        ) : (
          <IconUser size={12} />
        )}
        <Text>{record.name}</Text>
      </Group>
    </Tooltip>
  ) : null;
}
