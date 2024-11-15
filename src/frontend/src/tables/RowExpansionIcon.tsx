import { ActionIcon } from '@mantine/core';
import { IconChevronDown, IconChevronRight } from '@tabler/icons-react';

export default function RowExpansionIcon({
  enabled,
  expanded
}: Readonly<{
  enabled: boolean;
  expanded: boolean;
}>) {
  return (
    <ActionIcon size='sm' variant='transparent' disabled={!enabled}>
      {expanded ? <IconChevronDown /> : <IconChevronRight />}
    </ActionIcon>
  );
}
