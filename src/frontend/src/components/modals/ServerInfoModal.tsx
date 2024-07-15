import { Trans } from '@lingui/macro';
import {
  Badge,
  Button,
  Divider,
  Group,
  Stack,
  Table,
  Title
} from '@mantine/core';
import { ContextModalProps } from '@mantine/modals';

import { useServerApiState } from '../../states/ApiState';
import { OnlyStaff } from '../items/OnlyStaff';

export function ServerInfoModal({
  context,
  id
}: ContextModalProps<{ modalBody: string }>) {
  const [server] = useServerApiState((state) => [state.server]);

  return (
    <Stack>
      <Divider />
      <Title order={5}>
        <Trans>Server</Trans>
      </Title>
      <Table>
        <Table.Tbody>
          <Table.Tr>
            <Table.Td>
              <Trans>Instance Name</Trans>
            </Table.Td>
            <Table.Td>{server.instance}</Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>Database</Trans>
            </Table.Td>
            <Table.Td>
              <OnlyStaff>{server.database}</OnlyStaff>
            </Table.Td>
          </Table.Tr>
          {server.debug_mode && (
            <Table.Tr>
              <Table.Td>
                <Trans>Debug Mode</Trans>
              </Table.Td>
              <Table.Td>
                <Trans>Server is running in debug mode</Trans>
              </Table.Td>
            </Table.Tr>
          )}
          {server.docker_mode && (
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
          {server?.worker_running == false && (
            <Table.Tr>
              <Table.Td>
                <Trans>Background Worker</Trans>
              </Table.Td>
              <Table.Td>
                <Badge color="red">
                  <Trans>Background worker not running</Trans>
                </Badge>
              </Table.Td>
            </Table.Tr>
          )}
          {server?.email_configured == false && (
            <Table.Tr>
              <Table.Td>
                <Trans>Email Settings</Trans>
              </Table.Td>
              <Table.Td>
                <Badge color="red">
                  <Trans>Email settings not configured</Trans>
                </Badge>
              </Table.Td>
            </Table.Tr>
          )}
        </Table.Tbody>
      </Table>
      <Title order={5}>
        <Trans>Version</Trans>
      </Title>
      <Table>
        <Table.Tbody>
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
        </Table.Tbody>
      </Table>
      <Divider />
      <Group justify="right">
        <Button
          color="red"
          onClick={() => {
            context.closeModal(id);
          }}
        >
          <Trans>Dismiss</Trans>
        </Button>
      </Group>
    </Stack>
  );
}
