import { ActionIcon, Center, Group, Text, Tooltip } from '@mantine/core';
import { IconServer } from '@tabler/icons-react';

import { useServerApiState } from '../../states/ApiState';
import { ColorToggle } from '../items/ColorToggle';
import { LanguageToggle } from '../items/LanguageToggle';

export function AuthFormOptions({
  hostname,
  toggleHostEdit
}: Readonly<{
  hostname: string;
  toggleHostEdit: () => void;
}>) {
  const [server] = useServerApiState((state) => [state.server]);

  return (
    <Center mx={'md'}>
      <Group>
        <ColorToggle />
        <LanguageToggle />
        {window.INVENTREE_SETTINGS.show_server_selector && (
          <Tooltip label={hostname}>
            <ActionIcon
              size='lg'
              variant='transparent'
              onClick={toggleHostEdit}
            >
              <IconServer />
            </ActionIcon>
          </Tooltip>
        )}
        <Text c={'dimmed'}>
          {server.version} | {server.apiVersion}
        </Text>
      </Group>
    </Center>
  );
}
