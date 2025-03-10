import {
  ActionIcon,
  Group,
  Tooltip,
  useMantineColorScheme
} from '@mantine/core';
import { IconMoonStars, IconSun } from '@tabler/icons-react';

import { t } from '@lingui/macro';
import { vars } from '../../theme';

export function ColorToggle() {
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();

  return (
    <Group justify='center'>
      <Tooltip label={t`Toggle color scheme`}>
        <ActionIcon
          onClick={toggleColorScheme}
          size='lg'
          style={{
            color:
              colorScheme === 'dark'
                ? vars.colors.yellow[4]
                : vars.colors.blue[6]
          }}
          variant='transparent'
        >
          {colorScheme === 'dark' ? <IconSun /> : <IconMoonStars />}
        </ActionIcon>
      </Tooltip>
    </Group>
  );
}
