import type { ApiFormFieldSet } from '@lib/types/Forms';
import { t } from '@lingui/core/macro';
import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { useApi } from '../contexts/ApiContext';
import { extractAvailableFields } from '../functions/forms';
import useDataOutput from './UseDataOutput';
import { useCreateApiFormModal } from './UseForm';

/**
 * Custom hook for managing data export functionality
 * This is intended to be used from a table or calendar view,
 * to export the data displayed in the table or calendar
 */
export default function useDataExport({
  url,
  enabled,
  filters,
  searchTerm
}: {
  url: string;
  enabled: boolean;
  filters: any;
  searchTerm?: string;
}) {
  const api = useApi();

  // Selected plugin to use for data export
  const [pluginKey, setPluginKey] = useState<string>('inventree-exporter');

  const [exportId, setExportId] = useState<number | undefined>(undefined);

  useDataOutput({
    title: t`Exporting Data`,
    id: exportId
  });

  // Construct a set of export parameters
  const exportParams = useMemo(() => {
    const queryParams: Record<string, any> = {
      export: true
    };

    if (!!pluginKey) {
      queryParams.export_plugin = pluginKey;
    }

    // Add in any additional parameters which have a defined value
    for (const [key, value] of Object.entries(filters ?? {})) {
      if (value != undefined) {
        queryParams[key] = value;
      }
    }

    if (!!searchTerm) {
      queryParams.search = searchTerm;
    }

    return queryParams;
  }, [pluginKey, filters, searchTerm]);

  const [exportDialogOpen, setExportDialogOpen] = useState<boolean>(false);

  // Fetch available export fields via OPTIONS request
  const extraExportFields = useQuery({
    enabled: !!url && enabled && exportDialogOpen,
    queryKey: ['export-fields', pluginKey, url, exportParams, exportDialogOpen],
    gcTime: 500,
    queryFn: () =>
      api
        .options(url, {
          params: exportParams
        })
        .then((response: any) => {
          return extractAvailableFields(response, 'GET') || {};
        })
  });

  // Construct a field set for the export form
  const exportFields: ApiFormFieldSet = useMemo(() => {
    const extraFields: ApiFormFieldSet = extraExportFields.data || {};

    const fields: ApiFormFieldSet = {
      export_format: {},
      export_plugin: {},
      ...extraFields
    };

    fields.export_format = {
      ...fields.export_format,
      required: true
    };

    fields.export_plugin = {
      ...fields.export_plugin,
      required: true,
      onValueChange: (value: string) => {
        if (!!value) {
          setPluginKey(value);
        }
      }
    };

    return fields;
  }, [extraExportFields]);

  // Modal for exporting data
  const exportModal = useCreateApiFormModal({
    url: url,
    queryParams: new URLSearchParams(exportParams),
    title: t`Export Data`,
    method: 'GET',
    fields: exportFields,
    submitText: t`Export`,
    successMessage: null,
    timeout: 30 * 1000,
    onOpen: () => {
      setExportDialogOpen(true);
    },
    onClose: () => {
      setExportDialogOpen(false);
    },
    onFormSuccess: (response: any) => {
      setExportId(response.pk);
      setPluginKey('inventree-exporter');
    }
  });

  return exportModal;
}
