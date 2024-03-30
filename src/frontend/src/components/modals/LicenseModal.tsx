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
import { ContextModalProps } from '@mantine/modals';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';
import { StylishText } from '../items/StylishText';

export function LicenceView(entries: any[]) {
  return (
    <Stack spacing="xs">
      <Divider />
      {entries?.length && (
        <Accordion variant="contained" defaultValue="-">
          {entries?.map((entry: any, index: number) => (
            <Accordion.Item key={index} value={`entry-${index}`}>
              <Accordion.Control>
                <Group position="apart" grow>
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
      )}
    </Stack>
  );
}

export function LicenseModal({}: ContextModalProps<{
  modalBody: string;
}>) {
  const { data, isFetching, isError } = useQuery({
    queryKey: ['license'],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.license))
        .then((res) => res.data ?? {})
        .catch(() => {})
  });

  return (
    <Stack spacing="xs">
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
        <Tabs defaultValue="backend">
          <Tabs.List>
            <Tabs.Tab value="backend">
              <Trans>Backend Packages</Trans>
            </Tabs.Tab>
            <Tabs.Tab value="frontend">
              <Trans>Frontend Packages</Trans>
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="backend">
            {LicenceView(data?.backend ?? [])}
          </Tabs.Panel>

          <Tabs.Panel value="frontend">
            {LicenceView(data?.frontend ?? [])}
          </Tabs.Panel>
        </Tabs>
      )}
    </Stack>
  );
}
