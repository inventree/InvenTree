import { Trans } from '@lingui/macro';
import { Anchor, Badge, Group, Stack, Table, Text, Title } from '@mantine/core';
import { ContextModalProps } from '@mantine/modals';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../App';
import { ApiPaths } from '../../enums/ApiEndpoints';
import { apiUrl, useServerApiState } from '../../states/ApiState';
import { useLocalState } from '../../states/LocalState';
import { useUserState } from '../../states/UserState';
import { CopyButton } from '../items/CopyButton';

type AboutLookupRef = {
  ref: string;
  title: JSX.Element;
  link?: string;
  copy?: boolean;
};

export function AboutInvenTreeModal({}: ContextModalProps<{
  modalBody: string;
}>) {
  const [user] = useUserState((state) => [state.user]);
  const { host } = useLocalState.getState();
  const [server] = useServerApiState((state) => [state.server]);

  if (user?.is_staff != true)
    return (
      <Text>
        <Trans>This information is only available for staff users</Trans>
      </Text>
    );

  const { isLoading, data } = useQuery({
    queryKey: ['version'],
    queryFn: () => api.get(apiUrl(ApiPaths.version)).then((res) => res.data)
  });

  function fillTable(
    lookup: AboutLookupRef[],
    data: any,
    alwaysLink: boolean = false
  ) {
    return lookup.map((map: AboutLookupRef, idx) => (
      <tr key={idx}>
        <td>{map.title}</td>
        <td>
          <Group position="apart" spacing="xs">
            {alwaysLink ? (
              <Anchor href={data[map.ref]} target="_blank">
                {data[map.ref]}
              </Anchor>
            ) : map.link ? (
              <Anchor href={map.link} target="_blank">
                {data[map.ref]}
              </Anchor>
            ) : (
              data[map.ref]
            )}
            {map.copy && <CopyButton value={data[map.ref]} />}
          </Group>
        </td>
      </tr>
    ));
  }
  /* renderer */
  if (isLoading) return <Trans>Loading</Trans>;

  const copyval = `InvenTree-Version: ${data.version.server}\nDjango Version: ${
    data.version.django
  }\n${
    data.version.commit_hash &&
    `Commit Hash: ${data.version.commit_hash}\nCommit Date: ${data.version.commit_date}\nCommit Branch: ${data.version.commit_branch}\n`
  }Database: ${server.database}\nDebug-Mode: ${
    server.debug_mode ? 'True' : 'False'
  }\nDeployed using Docker: ${
    server.docker_mode ? 'True' : 'False'
  }\nPlatform: ${server.platform}\nInstaller: ${server.installer}\n${
    server.target && `Target: ${server.target}\n`
  }Active plugins: ${JSON.stringify(server.active_plugins)}`;
  return (
    <Stack>
      <Group>
        <Text>
          <Trans>Your InvenTree version status is</Trans>
        </Text>
        {data.dev ? (
          <Badge color="blue">
            <Trans>Development Version</Trans>
          </Badge>
        ) : data.up_to_date ? (
          <Badge color="green">
            <Trans>Up to Date</Trans>
          </Badge>
        ) : (
          <Badge color="teal">
            <Trans>Update Available</Trans>
          </Badge>
        )}
      </Group>
      <Title order={5}>
        <Trans>Version Information</Trans>
      </Title>
      <Table>
        <tbody>
          {fillTable(
            [
              {
                ref: 'server',
                title: <Trans>InvenTree Version</Trans>,
                link: 'https://github.com/inventree/InvenTree/releases',
                copy: true
              },
              {
                ref: 'commit_hash',
                title: <Trans>Commit Hash</Trans>,
                copy: true
              },
              {
                ref: 'commit_date',
                title: <Trans>Commit Date</Trans>,
                copy: true
              },
              {
                ref: 'commit_branch',
                title: <Trans>Commit Branch</Trans>,
                copy: true
              },
              {
                ref: 'api',
                title: <Trans>API Version</Trans>,
                link: `${host}api-doc/`
              },
              { ref: 'python', title: <Trans>Python Version</Trans> },
              {
                ref: 'django',
                title: <Trans>Django Version</Trans>,
                link: 'https://www.djangoproject.com/',
                copy: true
              }
            ],
            data.version
          )}
        </tbody>
      </Table>
      <Title order={5}>
        <Trans>Links</Trans>
      </Title>
      <Table>
        <tbody>
          {fillTable(
            [
              { ref: 'doc', title: <Trans>InvenTree Documentation</Trans> },
              { ref: 'code', title: <Trans>View Code on GitHub</Trans> },
              { ref: 'credit', title: <Trans>Credits</Trans> },
              { ref: 'app', title: <Trans>Mobile App</Trans> },
              { ref: 'bug', title: <Trans>Submit Bug Report</Trans> }
            ],
            data.links,
            true
          )}
        </tbody>
      </Table>
      <Group>
        <CopyButton
          value={copyval}
          label={<Trans>Copy version information</Trans>}
        />
      </Group>
    </Stack>
  );
}
