import { ActionButton } from '@lib/components/ActionButton';
import { t } from '@lingui/core/macro';
import type { FloatingPosition } from '@mantine/core';
import { InvenTreeIcon } from '../../functions/icons';

export default function RemoveRowButton({
  onClick,
  disabled,
  tooltip = t`Remove this row`,
  tooltipAlignment
}: Readonly<{
  onClick: () => void;
  disabled?: boolean;
  tooltip?: string;
  tooltipAlignment?: FloatingPosition;
}>) {
  return (
    <ActionButton
      onClick={onClick}
      disabled={disabled}
      icon={<InvenTreeIcon icon='square_x' />}
      tooltip={tooltip}
      tooltipAlignment={tooltipAlignment ?? 'top-end'}
      color='red'
    />
  );
}
