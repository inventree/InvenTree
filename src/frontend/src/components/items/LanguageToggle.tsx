import { ActionIcon, Group, Tooltip } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconLanguage } from '@tabler/icons-react';

import { t } from '@lingui/macro';
import { LanguageSelect } from './LanguageSelect';

export function LanguageToggle() {
  const [open, toggle] = useDisclosure();

  return (
    <Group
      justify='center'
      style={{
        border: open === true ? '1px dashed' : '',
        margin: open === true ? 2 : 12,
        padding: open === true ? 8 : 0
      }}
    >
      <Tooltip label={t`Select language`}>
        <ActionIcon
          onClick={() => toggle.toggle()}
          size='lg'
          variant='transparent'
          aria-label='Language toggle'
        >
          <IconLanguage />
        </ActionIcon>
      </Tooltip>
      {open && (
        <Group>
          <LanguageSelect />
        </Group>
      )}
    </Group>
  );
}
