import { ActionIcon } from '@mantine/core';
import { IconChevronDown, IconChevronRight } from '@tabler/icons-react';

export default function RowExpansionIcon({
  enabled,
  expanded,
  onClick,
  ariaLabel
}: Readonly<{
  enabled: boolean;
  expanded: boolean;
  onClick?: (event: React.MouseEvent) => void;
  ariaLabel?: string;
}>) {
  return (
    <ActionIcon
      aria-label={ariaLabel}
      size='sm'
      variant='transparent'
      disabled={!enabled}
      onClick={onClick}
    >
      {expanded ? <IconChevronDown /> : <IconChevronRight />}
    </ActionIcon>
  );
}
