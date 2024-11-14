import { t } from '@lingui/macro';

import { InvenTreeIcon } from '../../functions/icons';
import { ActionButton } from './ActionButton';

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
      tooltipAlignment='top'
      color='red'
    />
  );
}
