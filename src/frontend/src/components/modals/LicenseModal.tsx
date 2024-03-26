import { Trans } from '@lingui/macro';
import { Accordion } from '@mantine/core';
import { ContextModalProps } from '@mantine/modals';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';

export function LicenseModal({}: ContextModalProps<{
  modalBody: string;
}>) {
  const { isLoading, data } = useQuery({
    queryKey: ['license'],
    queryFn: () => api.get(apiUrl(ApiEndpoints.license)).then((res) => res.data)
  });
  if (isLoading) return <Trans>Loading</Trans>;
  return (
    <Accordion variant="contained" defaultValue="customization">
      {Object.keys(data).map((item, key) => (
        <Accordion.Item key={key} value={item}>
          <Accordion.Control>{item}</Accordion.Control>
          <Accordion.Panel>
            <p style={{ whiteSpace: 'pre-line' }}>{data[item]}</p>
          </Accordion.Panel>
        </Accordion.Item>
      ))}
    </Accordion>
  );
}
