import { Trans } from '@lingui/react/macro';
import { Badge, Button, Divider, Group, Stack, Table } from '@mantine/core';
import type { ContextModalProps } from '@mantine/modals';

import { useShallow } from 'zustand/react/shallow';
import { useSystemStatus } from '../../hooks/UseAdminMessages';
import { useServerApiState } from '../../states/ServerApiState';
import { OnlyStaff } from '../items/OnlyStaff';

export function ServerInfoModal({
  context,
  id
}: ContextModalProps<{ modalBody: string }>) {
  const [server] = useServerApiState(useShallow((state) => [state.server]));

  // Deployment details are staff-only (undefined for non-staff users)
  const { server: status } = useSystemStatus();

  return (
    <Stack>
      <Divider />
      <Table striped>
        <Table.Tbody>
          <Table.Tr>
            <Table.Td>
              <Trans>Instance Name</Trans>
            </Table.Td>
            <Table.Td>{server.instance}</Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>Server Version</Trans>
            </Table.Td>
            <Table.Td>{server.version}</Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>API Version</Trans>
            </Table.Td>
            <Table.Td>{server.apiVersion}</Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>Database</Trans>
            </Table.Td>
            <Table.Td>
              <OnlyStaff>{status?.database}</OnlyStaff>
            </Table.Td>
          </Table.Tr>
          {status?.debug_mode && (
            <Table.Tr>
              <Table.Td>
                <Trans>Debug Mode</Trans>
              </Table.Td>
              <Table.Td>
                <Group justify='space-between'>
                  <Badge color='red'>INVE-W4</Badge>
                  <Trans>Server is running in debug mode</Trans>
                </Group>
              </Table.Td>
            </Table.Tr>
          )}
          {status?.docker_mode && (
            <Table.Tr>
              <Table.Td>
                <Trans>Docker Mode</Trans>
              </Table.Td>
              <Table.Td>
                <Trans>Server is deployed using docker</Trans>
              </Table.Td>
            </Table.Tr>
          )}
          <Table.Tr>
            <Table.Td>
              <Trans>Plugin Support</Trans>
            </Table.Td>
            <Table.Td>
              <Badge color={server.plugins_enabled ? 'green' : 'red'}>
                {server.plugins_enabled ? (
                  <Trans>Plugin support enabled</Trans>
                ) : (
                  <Trans>Plugin support disabled</Trans>
                )}
              </Badge>
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>Server status</Trans>
            </Table.Td>
            <Table.Td>
              <OnlyStaff>
                <Badge color={server.system_health ? 'green' : 'yellow'}>
                  {server.system_health ? (
                    <Trans>Healthy</Trans>
                  ) : (
                    <Trans>Issues detected</Trans>
                  )}
                </Badge>
              </OnlyStaff>
            </Table.Td>
          </Table.Tr>
          {status?.worker_running === false && (
            <Table.Tr>
              <Table.Td>
                <Trans>Background Worker</Trans>
              </Table.Td>
              <Table.Td>
                <Group justify='space-between'>
                  <Badge color='red'>INVE-W5</Badge>
                  <Trans>The background worker process is not running</Trans>
                </Group>
              </Table.Td>
            </Table.Tr>
          )}
          {status?.email_configured === false && (
            <Table.Tr>
              <Table.Td>
                <Trans>Email Settings</Trans>
              </Table.Td>
              <Table.Td>
                <Group justify='space-between'>
                  <Badge color='red'>INVE-W7</Badge>
                  <Trans>Email settings not configured.</Trans>
                </Group>
              </Table.Td>
            </Table.Tr>
          )}
        </Table.Tbody>
      </Table>
      <Divider />
      <Group justify='right'>
        <Button
          onClick={() => {
            context.closeModal(id);
          }}
        >
          <Trans>Close</Trans>
        </Button>
      </Group>
    </Stack>
  );
}
