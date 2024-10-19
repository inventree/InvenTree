import { ActionIcon, Group } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconLanguage } from '@tabler/icons-react';

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
      <ActionIcon
        onClick={() => toggle.toggle()}
        size='lg'
        variant='transparent'
      >
        <IconLanguage />
      </ActionIcon>
      {open && (
        <Group>
          <LanguageSelect />
        </Group>
      )}
    </Group>
  );
}
