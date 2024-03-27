import { Trans, t } from '@lingui/macro';
import {
  Accordion,
  Alert,
  Divider,
  LoadingOverlay,
  Stack,
  Text
} from '@mantine/core';
import { ContextModalProps, closeModal } from '@mantine/modals';
import { notifications } from '@mantine/notifications';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';

export function LicenseModal({}: ContextModalProps<{
  modalBody: string;
}>) {
  const { data, isFetching, isError } = useQuery({
    queryKey: ['license'],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.license))
        .then((res) => res.data)
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
        <Accordion variant="contained" defaultValue="customization">
          {Object.keys(data ?? []).map((item, key) => (
            <Accordion.Item key={key} value={item}>
              <Accordion.Control>{item}</Accordion.Control>
              <Accordion.Panel>
                <p style={{ whiteSpace: 'pre-line' }}>{data[item]}</p>
              </Accordion.Panel>
            </Accordion.Item>
          ))}
        </Accordion>
      )}
    </Stack>
  );
}
