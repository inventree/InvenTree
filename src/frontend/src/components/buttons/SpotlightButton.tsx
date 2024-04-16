import { t } from '@lingui/macro';
import { ActionIcon } from '@mantine/core';
import { spotlight } from '@mantine/spotlight';
import { IconCommand } from '@tabler/icons-react';

/**
 * A button which opens the quick command modal
 */
export function SpotlightButton() {
  return (
    <ActionIcon onClick={() => spotlight.open()} title={t`Open spotlight`}>
      <IconCommand />
    </ActionIcon>
  );
}
