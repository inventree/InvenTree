import { t } from '@lingui/core/macro';

import { ActionButton } from '@lib/components/ActionButton';
import type { FloatingPosition } from '@mantine/core';
import { InvenTreeIcon } from '../../functions/icons';

export default function RemoveRowButton({
  onClick,
  tooltip = t`Remove this row`,
  tooltipAlignment
}: Readonly<{
  onClick: () => void;
  tooltip?: string;
  tooltipAlignment?: FloatingPosition;
}>) {
  return (
    <ActionButton
      onClick={onClick}
      icon={<InvenTreeIcon icon='square_x' />}
      tooltip={tooltip}
      tooltipAlignment={tooltipAlignment ?? 'top-end'}
      color='red'
    />
  );
}
