import { t } from '@lingui/macro';
import { Anchor, Group, MantineSize, Text, Tooltip } from '@mantine/core';
import {
  IconQuestionMark,
  IconUser,
  IconUsersGroup
} from '@tabler/icons-react';

function OwnerIcon({
  record,
  size
}: {
  record: any;
  size: MantineSize | number;
}) {
  switch (record.label) {
    case t`group`:
      return <IconUsersGroup size={size} />;
    case t`user`:
      return <IconUser size={size} />;
    default:
      return <IconQuestionMark size={size} />;
  }
}

export function ownerRenderer(record: any) {
  return record ? (
    <Tooltip label={record.label} position="bottom">
      <Group spacing={0}>
        <OwnerIcon record={record} size={16} />
        <Text>{record.name}</Text>
      </Group>
    </Tooltip>
  ) : null;
}
