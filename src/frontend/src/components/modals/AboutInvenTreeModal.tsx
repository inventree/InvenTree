import { Trans, t } from '@lingui/macro';
import {
  Anchor,
  Badge,
  Button,
  Divider,
  Group,
  Space,
  Stack,
  Table,
  Text
} from '@mantine/core';
import type { ContextModalProps } from '@mantine/modals';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { generateUrl } from '../../functions/urls';
import { apiUrl, useServerApiState } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { CopyButton } from '../buttons/CopyButton';
import { StylishText } from '../items/StylishText';

type AboutLookupRef = {
  ref: string;
  title: JSX.Element;
  link?: string;
  copy?: boolean;
};

export function AboutInvenTreeModal({
  context,
  id
}: ContextModalProps<{
  modalBody: string;
}>) {
  const [user] = useUserState((state) => [state.user]);
  const [server] = useServerApiState((state) => [state.server]);

  if (user?.is_staff != true)
    return (
      <Text>
        <Trans>This information is only available for staff users</Trans>
      </Text>
    );

  const { isLoading, data } = useQuery({
    queryKey: ['version'],
    queryFn: () => api.get(apiUrl(ApiEndpoints.version)).then((res) => res.data)
  });

  function fillTable(lookup: AboutLookupRef[], data: any, alwaysLink = false) {
    return lookup.map((map: AboutLookupRef, idx) => (
      <Table.Tr key={idx}>
        <Table.Td>{map.title}</Table.Td>
        <Table.Td>
          <Group justify='space-between' gap='xs'>
            {alwaysLink ? (
              <Anchor href={data[map.ref]} target='_blank'>
                {data[map.ref]}
              </Anchor>
            ) : map.link ? (
              <Anchor href={map.link} target='_blank'>
                {data[map.ref]}
              </Anchor>
            ) : (
              data[map.ref]
            )}
            {map.copy && <CopyButton value={data[map.ref]} />}
          </Group>
        </Table.Td>
      </Table.Tr>
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
      <Divider />
      <Group justify='space-between' wrap='nowrap'>
        <StylishText size='lg'>
          <Trans>Version Information</Trans>
        </StylishText>
        {data.dev ? (
          <Badge color='blue'>
            <Trans>Development Version</Trans>
          </Badge>
        ) : data.up_to_date ? (
          <Badge color='green'>
            <Trans>Up to Date</Trans>
          </Badge>
        ) : (
          <Badge color='teal'>
            <Trans>Update Available</Trans>
          </Badge>
        )}
      </Group>
      <Table striped>
        <Table.Tbody>
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
                link: generateUrl('/api-doc/'),
                copy: true
              },
              {
                ref: 'python',
                title: <Trans>Python Version</Trans>,
                copy: true
              },
              {
                ref: 'django',
                title: <Trans>Django Version</Trans>,
                link: 'https://www.djangoproject.com/',
                copy: true
              }
            ],
            data.version
          )}
        </Table.Tbody>
      </Table>
      <Divider />
      <StylishText size='lg'>
        <Trans>Links</Trans>
      </StylishText>
      <Table striped>
        <Table.Tbody>
          {fillTable(
            [
              { ref: 'doc', title: <Trans>Documentation</Trans> },
              { ref: 'code', title: <Trans>Source Code</Trans> },
              { ref: 'credit', title: <Trans>Credits</Trans> },
              { ref: 'app', title: <Trans>Mobile App</Trans> },
              { ref: 'bug', title: <Trans>Submit Bug Report</Trans> }
            ],
            data.links,
            true
          )}
        </Table.Tbody>
      </Table>
      <Divider />
      <Group justify='space-between'>
        <CopyButton value={copyval} label={t`Copy version information`} />
        <Space />
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
