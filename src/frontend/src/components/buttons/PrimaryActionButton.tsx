import { Button, Tooltip } from '@mantine/core';

import { InvenTreeIcon, type InvenTreeIconType } from '../../functions/icons';

/**
 * A "primary action" button for display on a page detail, (for example)
 */
export default function PrimaryActionButton({
  title,
  tooltip,
  icon,
  color,
  hidden,
  onClick
}: Readonly<{
  title: string;
  tooltip?: string;
  icon?: InvenTreeIconType;
  color?: string;
  hidden?: boolean;
  onClick: () => void;
}>) {
  if (hidden) {
    return null;
  }

  return (
    <Tooltip label={tooltip ?? title} position='bottom' hidden={!tooltip}>
      <Button
        leftSection={icon && <InvenTreeIcon icon={icon} />}
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
