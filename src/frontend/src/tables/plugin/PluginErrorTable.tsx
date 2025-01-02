import { t } from '@lingui/macro';
import { Code } from '@mantine/core';
import { useMemo } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import type { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

export interface PluginRegistryErrorI {
  id: number;
  stage: string;
  name: string;
  message: string;
}

/**
 * Table displaying list of plugin registry errors
 */
export default function PluginErrorTable() {
  const table = useTable('registryErrors', 'id');

  const registryErrorTableColumns: TableColumn<PluginRegistryErrorI>[] =
    useMemo(
      () => [
        {
          accessor: 'stage',
          title: t`Stage`
        },
        {
          accessor: 'name',
          title: t`Name`
        },
        {
          accessor: 'message',
          title: t`Message`,
          render: (row) => <Code>{row.message}</Code>
        }
      ],
      []
    );

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.plugin_registry_status)}
      tableState={table}
      columns={registryErrorTableColumns}
      props={{
        dataFormatter: (data: any) =>
          data.registry_errors.map((e: any, i: number) => ({ id: i, ...e })),
        enableDownload: false,
        enableFilters: false,
        enableSearch: false
      }}
    />
  );
}
