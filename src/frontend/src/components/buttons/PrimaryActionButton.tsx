import type { InvenTreeIconType } from '@lib/types/Icons';
import { Button, Tooltip } from '@mantine/core';
import { InvenTreeIcon } from '../../functions/icons';

/**
 * A "primary action" button for display on a page detail, (for example)
 */
export default function PrimaryActionButton({
  title,
  tooltip,
  icon,
  color,
  hidden,
  onClick,
  leftSection
}: Readonly<{
  title: string;
  tooltip?: string;
  icon?: keyof InvenTreeIconType;
  color?: string;
  hidden?: boolean;
  onClick: () => void;
  leftSection?: React.ReactNode;
}>) {
  if (hidden) {
    return null;
  }

  return (
    <Tooltip label={tooltip ?? title} position='bottom' hidden={!tooltip}>
      <Button
        leftSection={leftSection ?? (icon && <InvenTreeIcon icon={icon} />)}
        color={color}
        radius='sm'
        p='xs'
        onClick={onClick}
      >
        {title}
      </Button>
    </Tooltip>
  );
}
