import { t } from '@lingui/macro';
import { IconDownload } from '@tabler/icons-react';
import { useMemo, useState } from 'react';

import { Button, Tooltip } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { api } from '../App';
import type { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';
import { useCreateApiFormModal } from '../hooks/UseForm';

export function DownloadAction({
  url,
  downloadCallback
}: Readonly<{
  url: string;
  downloadCallback: (fileFormat: string) => void;
}>) {
  // Selected plugin to use for data export
  const [pluginKey, setPluginKey] = useState<string>('');

  // Fetch available export fields via OPTIONS request
  const extraExportFields = useQuery({
    enabled: true,
    queryKey: ['exportFields', pluginKey, url],
    gcTime: 500,
    queryFn: () =>
      api
        .options(url, {
          params: {
            export: true,
            export_plugin: pluginKey || undefined
          }
        })
        .then((response: any) => {
          console.log('OPTIONS:', response);
          return {};
        })
        .catch(() => {
          return {};
        })
  });

  const exportFields: ApiFormFieldSet = useMemo(() => {
    const extraFields: ApiFormFieldSet = extraExportFields.data || {};

    return {
      export_format: {},
      export_plugin: {
        onValueChange: (value: string) => {
          setPluginKey(value);
        }
      },
      ...extraFields
    };
  }, [extraExportFields.data]);

  const exportModal = useCreateApiFormModal({
    url: url,
    queryParams: new URLSearchParams({ export: 'true' }),
    title: t`Export Data`,
    fields: exportFields,
    submitText: t`Export`,
    successMessage: t`Data exported successfully`,
    onFormSuccess: (data: any) => {
      setPluginKey('');
    }
  });

  return (
    <>
      {exportModal.modal}
      <Tooltip label={t`Download data`} position='bottom'>
        <Button
          variant='transparent'
          aria-label='export-data'
          onClick={exportModal.open}
        >
          <IconDownload />
        </Button>
      </Tooltip>
    </>
  );
}
