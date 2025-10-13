import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
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

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { useShallow } from 'zustand/react/shallow';
import { api } from '../../App';
import { generateUrl } from '../../functions/urls';
import { useServerApiState } from '../../states/ServerApiState';
import { useUserState } from '../../states/UserState';
import { CopyButton } from '../buttons/CopyButton';
import { StylishText } from '../items/StylishText';

import type { JSX } from 'react';

type AboutLookupRef = {
  ref: string;
  title: JSX.Element;
  link?: string;
  copy?: boolean;
};

export function AboutInvenTreeModal({
  context,
  id,
  innerProps
}: Readonly<
  ContextModalProps<{
    modalBody: string;
  }>
>) {
  const [user] = useUserState(useShallow((state) => [state.user]));

  if (!user?.is_staff)
    return (
      <Text>
        <Trans>This information is only available for staff users</Trans>
      </Text>
    );
  return <AboutContent context={context} id={id} innerProps={innerProps} />;
}

const AboutContent = ({
  context,
  id
}: Readonly<
  ContextModalProps<{
    modalBody: string;
  }>
>) => {
  const [server] = useServerApiState(useShallow((state) => [state.server]));
  const { isLoading, data } = useQuery({
    queryKey: ['version'],
    queryFn: () => api.get(apiUrl(ApiEndpoints.version)).then((res) => res.data)
  });

  function fillTable(lookup: AboutLookupRef[], data: any, alwaysLink = false) {
    return lookup
      .filter((entry: AboutLookupRef) => !!data[entry.ref])
      .map((entry: AboutLookupRef, idx) => (
        <Table.Tr key={idx}>
          <Table.Td>{entry.title}</Table.Td>
          <Table.Td>
            <Group justify='space-between' gap='xs'>
              {alwaysLink ? (
                <Anchor href={data[entry.ref]} target='_blank'>
                  {data[entry.ref]}
                </Anchor>
              ) : entry.link ? (
                <Anchor href={entry.link} target='_blank'>
                  {data[entry.ref]}
                </Anchor>
              ) : (
                data[entry.ref]
              )}
              {entry.copy && <CopyButton value={data[entry.ref]} />}
            </Group>
          </Table.Td>
        </Table.Tr>
      ));
  }
  /* renderer */
  if (isLoading) return <Trans>Loading</Trans>;

  const commit_set: boolean =
    data.version.commit_hash && data.version.commit_date;

  const copyval = `InvenTree-Version: ${data.version.server}\nDjango Version: ${
    data.version.django
  }\n${
    commit_set
      ? `Commit Hash: ${data.version.commit_hash}\nCommit Date: ${data.version.commit_date}\nCommit Branch: ${data.version.commit_branch}\n`
      : ''
  }Database: ${server.database}\nDebug-Mode: ${
    server.debug_mode ? 'True' : 'False'
  }\nDeployed using Docker: ${
    server.docker_mode ? 'True' : 'False'
  }\nPlatform: ${server.platform}\nInstaller: ${server.installer ? server.installer : ''}\n${
    server.target ? `Target: ${server.target}\n` : ''
  }Active plugins: ${JSON.stringify(server.active_plugins)}`;

  const tableData = [
    {
      ref: 'server',
      title: <Trans>InvenTree Version</Trans>,
      link: 'https://github.com/inventree/InvenTree/releases',
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
  ];
  if (commit_set) {
    tableData.push(
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
      }
    );
  }

  return (
    <Stack>
      <Divider />
      <Group justify='space-between' wrap='nowrap'>
        <StylishText size='lg'>
          <Trans>Version Information</Trans>
        </StylishText>
        {renderVersionBadge(data)}
      </Group>
      <Table striped>
        <Table.Tbody>{fillTable(tableData, data.version)}</Table.Tbody>
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
};

function renderVersionBadge(data: any) {
  const badgeType = () => {
    if (data.dev) {
      return { color: 'blue', label: <Trans>Development Version</Trans> };
    } else if (data.up_to_date) {
      return { color: 'green', label: <Trans>Up to Date</Trans> };
    } else {
      return { color: 'teal', label: <Trans>Update Available</Trans> };
    }
  };
  const { color, label } = badgeType();
  return <Badge color={color}>{label}</Badge>;
}
