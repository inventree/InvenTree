import { Trans } from '@lingui/macro';
import { Badge, Button, Stack, Table, Title } from '@mantine/core';
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
      <Title order={5}>
        <Trans>Server</Trans>
      </Title>
      <Table>
        <tbody>
          <tr>
            <td>
              <Trans>Instance Name</Trans>
            </td>
            <td>{server.instance}</td>
          </tr>
          <tr>
            <td>
              <Trans>Database</Trans>
            </td>
            <td>
              <OnlyStaff>{server.database}</OnlyStaff>
            </td>
          </tr>
          {server.debug_mode && (
            <tr>
              <td>
                <Trans>Debug Mode</Trans>
              </td>
              <td>
                <Trans>Server is running in debug mode</Trans>
              </td>
            </tr>
          )}
          {server.docker_mode && (
            <tr>
              <td>
                <Trans>Docker Mode</Trans>
              </td>
              <td>
                <Trans>Server is deployed using docker</Trans>
              </td>
            </tr>
          )}
          <tr>
            <td>
              <Trans>Plugin Support</Trans>
            </td>
            <td>
              <Badge color={server.plugins_enabled ? 'green' : 'red'}>
                {server.plugins_enabled ? (
                  <Trans>Plugin support enabled</Trans>
                ) : (
                  <Trans>Plugin support disabled</Trans>
                )}
              </Badge>
            </td>
          </tr>
          <tr>
            <td>
              <Trans>Server status</Trans>
            </td>
            <td>
              <OnlyStaff>
                <Badge color={server.system_health ? 'green' : 'yellow'}>
                  {server.system_health ? (
                    <Trans>Healthy</Trans>
                  ) : (
                    <Trans>Issues detected</Trans>
                  )}
                </Badge>
              </OnlyStaff>
            </td>
          </tr>
          {server.worker_running != true && (
            <tr>
              <td>
                <Trans>Background Worker</Trans>
              </td>
              <td>
                <Badge color="red">
                  <Trans>Background worker not running</Trans>
                </Badge>
              </td>
            </tr>
          )}
          {server.email_configured != true && (
            <tr>
              <td>
                <Trans>Email Settings</Trans>
              </td>
              <td>
                <Badge color="red">
                  <Trans>Email settings not configured</Trans>
                </Badge>
              </td>
            </tr>
          )}
        </tbody>
      </Table>
      <Title order={5}>
        <Trans>Version</Trans>
      </Title>
      <Table>
        <tbody>
          <tr>
            <td>
              <Trans>Server Version</Trans>
            </td>
            <td>{server.version}</td>
          </tr>
          <tr>
            <td>
              <Trans>API Version</Trans>
            </td>
            <td>{server.apiVersion}</td>
          </tr>
        </tbody>
      </Table>
      <Button
        color="red"
        variant="outline"
        onClick={() => {
          context.closeModal(id);
        }}
      >
        <Trans>Close modal</Trans>
      </Button>
    </Stack>
  );
}
