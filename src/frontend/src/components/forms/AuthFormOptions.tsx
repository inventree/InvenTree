import { Center, Group, Tooltip } from '@mantine/core';
import { IconServer } from '@tabler/icons-react';

import { ColorToggle } from '../items/ColorToggle';
import { LanguageToggle } from '../items/LanguageToggle';

export function AuthFormOptions({
  hostname,
  toggleHostEdit
}: {
  hostname: string;
  toggleHostEdit: () => void;
}) {
  return (
    <Center mx={'md'}>
      <Group>
        <ColorToggle />
        <LanguageToggle />
        <Tooltip label={hostname}>
          <IconServer onClick={toggleHostEdit} />
        </Tooltip>
      </Group>
    </Center>
  );
}
