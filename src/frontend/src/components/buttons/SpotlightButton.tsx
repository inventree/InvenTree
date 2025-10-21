import { t } from '@lingui/core/macro';
import { ActionIcon, Tooltip } from '@mantine/core';
import { IconCommand } from '@tabler/icons-react';

import { firstSpotlight } from '../nav/Layout';

/**
 * A button which opens the quick command modal
 */
export function SpotlightButton() {
  return (
    <Tooltip position='bottom-end' label={t`Open spotlight`}>
      <ActionIcon
        onClick={() => firstSpotlight.open()}
        variant='transparent'
        aria-label='open-spotlight'
      >
        <IconCommand />
      </ActionIcon>
    </Tooltip>
  );
}
