import { t } from '@lingui/core/macro';

import { ActionButton } from '@lib/components/ActionButton';
import { InvenTreeIcon } from '../../functions/icons';

export default function RemoveRowButton({
  onClick,
  tooltip = t`Remove this row`
}: Readonly<{
  onClick: () => void;
  tooltip?: string;
}>) {
  return (
    <ActionButton
      onClick={onClick}
      icon={<InvenTreeIcon icon='square_x' />}
      tooltip={tooltip}
      tooltipAlignment='top-end'
      color='red'
    />
  );
}
