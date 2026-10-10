import { t } from '@lingui/core/macro';
import { ActionIcon, Tooltip } from '@mantine/core';
import { IconCommand } from '@tabler/icons-react';

import { useLocalLibState } from '@lib/states/LocalLibState';
import { firstSpotlight, searchShortcutKey } from '../nav/Layout';

/**
 * A button which opens the quick command modal
 */
export function SpotlightButton({ hotkey = false }: { hotkey?: boolean }) {
  if (hotkey) {
    useLocalLibState
      .getState()
      .addHotkeys([[searchShortcutKey, t`Open spotlight`]]);
  }
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
