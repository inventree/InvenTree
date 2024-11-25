import { t } from '@lingui/macro';
import { ActionIcon } from '@mantine/core';
import { IconCommand } from '@tabler/icons-react';

import { firstSpotlight } from '../nav/Layout';

/**
 * A button which opens the quick command modal
 */
export function SpotlightButton() {
  return (
    <ActionIcon
      onClick={() => firstSpotlight.open()}
      title={t`Open spotlight`}
      variant='transparent'
      aria-label='open-spotlight'
    >
      <IconCommand />
    </ActionIcon>
  );
}
