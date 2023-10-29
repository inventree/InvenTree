import { Trans } from '@lingui/macro';
import { Badge, Button, Stack, Table, Title } from '@mantine/core';
import { ContextModalProps } from '@mantine/modals';

import { useServerApiState } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';

export function ServerInfoModal({
  context,
  id
}: ContextModalProps<{ modalBody: string }>) {
  const [server] = useServerApiState((state) => [state.server]);
  const [user] = useUserState((state) => [state.user]);

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
