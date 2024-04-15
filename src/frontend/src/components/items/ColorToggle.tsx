import { ActionIcon, Group, useMantineColorScheme } from '@mantine/core';
import { IconMoonStars, IconSun } from '@tabler/icons-react';

import { vars } from '../../theme';

export function ColorToggle() {
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
  //const computedColorScheme = useComputedColorScheme('light', {
  //  getInitialValueInEffect: true
  //});

  return (
    <Group justify="center">
      <ActionIcon
        onClick={toggleColorScheme}
        size="lg"
        style={{
          color:
            colorScheme === 'dark' ? vars.colors.yellow[4] : vars.colors.blue[6]
        }}
        variant="default"
      >
        {colorScheme === 'dark' ? <IconSun /> : <IconMoonStars />}
      </ActionIcon>
    </Group>
  );
}
