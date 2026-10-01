import { ActionIcon, Group, Text, Tooltip } from '@mantine/core';
import { IconServer } from '@tabler/icons-react';

import { t } from '@lingui/core/macro';
import { useShallow } from 'zustand/react/shallow';
import { useServerApiState } from '../../states/ServerApiState';
import { ColorToggle } from '../items/ColorToggle';
import { LanguageToggle } from '../items/LanguageToggle';

export function AuthFormOptions({
  hostname,
  toggleHostEdit
}: Readonly<{
  hostname: string;
  toggleHostEdit: () => void;
}>) {
  const [server] = useServerApiState(useShallow((state) => [state.server]));

  return (
    <Group gap={6} align='center' wrap='nowrap'>
      <ColorToggle />
      <LanguageToggle />
      {window.INVENTREE_SETTINGS.show_server_selector && (
        <Tooltip label={hostname || t`Select Server`} position='top'>
          <ActionIcon
            size='lg'
            variant='subtle'
            onClick={toggleHostEdit}
            aria-label={t`Server: ${hostname}`}
          >
            <IconServer size={20} />
          </ActionIcon>
        </Tooltip>
      )}
      {(server.version || server.apiVersion) ? (
        <Text size='xs' className='auth-overlay-version-badge'>
          {server.version ? `v${server.version}` : ''}
          {server.version && server.apiVersion ? ' • ' : ''}
          {server.apiVersion ? `API ${server.apiVersion}` : ''}
        </Text>
      ) : null}
    </Group>
  );
}
