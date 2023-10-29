import { Trans } from '@lingui/macro';
import {
  Anchor,
  Badge,
  Button,
  Group,
  Stack,
  Table,
  Text,
  Title
} from '@mantine/core';
import { ContextModalProps } from '@mantine/modals';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../App';
import { ApiPaths, apiUrl } from '../../states/ApiState';
import { useLocalState } from '../../states/LocalState';
import { useUserState } from '../../states/UserState';

type AboutLookupRef = {
  ref: string;
  title: JSX.Element;
  link?: string;
};

export function AboutInvenTreeModal({
  context,
  id
}: ContextModalProps<{ modalBody: string }>) {
  const [user] = useUserState((state) => [state.user]);
  const { host } = useLocalState.getState();

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
        </td>
      </tr>
    ));
  }
  /* renderer */
  if (isLoading) return <Trans>Loading</Trans>;

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
        <Trans>Server Versions</Trans>
      </Title>
      <Table>
        <tbody>
          {fillTable(
            [
              {
                ref: 'server',
                title: <Trans>InvenTree Version</Trans>,
                link: 'https://github.com/inventree/InvenTree/releases'
              },
              { ref: 'commit_hash', title: <Trans>Commit Hash</Trans> },
              { ref: 'commit_date', title: <Trans>Commit Date</Trans> },
              { ref: 'commit_branch', title: <Trans>Commit Branch</Trans> },
              {
                ref: 'api',
                title: <Trans>API Version</Trans>,
                link: `${host}api-doc/`
              },
              { ref: 'python', title: <Trans>Python Version</Trans> },
              {
                ref: 'django',
                title: <Trans>Django Version</Trans>,
                link: 'https://www.djangoproject.com/'
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
      Development Version
      <Group>
        <Button color="gray" variant="outline">
          <Trans>copy version information</Trans>
        </Button>
      </Group>
    </Stack>
  );
}
