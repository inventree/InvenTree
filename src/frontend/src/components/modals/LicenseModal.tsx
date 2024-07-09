import { Trans, t } from '@lingui/macro';
import {
  Accordion,
  Alert,
  Divider,
  Group,
  LoadingOverlay,
  Space,
  Stack,
  Tabs,
  Text
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';

export function LicenceView(entries: Readonly<any[]>) {
  return (
    <Stack gap="xs">
      <Divider />
      {entries?.length > 0 ? (
        <Accordion variant="contained" defaultValue="-">
          {entries?.map((entry: any, index: number) => (
            <Accordion.Item
              key={entry.name + entry.license + entry.version}
              value={`entry-${index}`}
            >
              <Accordion.Control>
                <Group justify="space-between" grow>
                  <Text>{entry.name}</Text>
                  <Text>{entry.license}</Text>
                  <Space />
                  <Text>{entry.version}</Text>
                </Group>
              </Accordion.Control>
              <Accordion.Panel style={{ whiteSpace: 'pre-line' }}>
                {entry.licensetext || t`No license text available`}
              </Accordion.Panel>
            </Accordion.Item>
          ))}
        </Accordion>
      ) : (
        <Text>
          <Trans>No Information provided - this is likely a server issue</Trans>
        </Text>
      )}
    </Stack>
  );
}

export function LicenseModal() {
  const { data, isFetching, isError } = useQuery({
    queryKey: ['license'],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.license))
        .then((res) => res.data ?? {})
        .catch(() => {})
  });

  const rspdata = !data ? [] : Object.keys(data ?? {});

  return (
    <Stack gap="xs">
      <Divider />
      <LoadingOverlay visible={isFetching} />
      {isFetching && (
        <Text>
          <Trans>Loading license information</Trans>
        </Text>
      )}
      {isError ? (
        <Alert color="red" title={t`Error`}>
          <Text>
            <Trans>Failed to fetch license information</Trans>
          </Text>
        </Alert>
      ) : (
        <Tabs defaultValue={rspdata[0] ?? ''}>
          <Tabs.List>
            {rspdata.map((key) => (
              <Tabs.Tab key={key} value={key}>
                <Trans>{key} Packages</Trans>
              </Tabs.Tab>
            ))}
          </Tabs.List>

          {rspdata.map((key) => (
            <Tabs.Panel key={key} value={key}>
              {LicenceView(data[key] ?? [])}
            </Tabs.Panel>
          ))}
        </Tabs>
      )}
    </Stack>
  );
}
