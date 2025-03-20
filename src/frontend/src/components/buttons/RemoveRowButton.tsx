import { t } from '@lingui/macro';

import { ActionButton } from '@lib/components';
import { InvenTreeIcon } from '@lib/components';

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
