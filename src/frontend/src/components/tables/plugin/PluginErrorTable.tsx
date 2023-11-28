import { t } from '@lingui/macro';
import { Code } from '@mantine/core';
import { useMemo } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../Column';
import { InvenTreeTable, InvenTreeTableProps } from '../InvenTreeTable';

export interface PluginRegistryErrorI {
  stage: string;
  name: string;
  message: string;
}

/**
 * Table displaying list of plugin registry errors
 */
export function PluginErrorTable({ props }: { props: InvenTreeTableProps }) {
  const table = useTable('registryErrors');

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
      url={apiUrl(ApiPaths.plugin_registry_status)}
      tableState={table}
      columns={registryErrorTableColumns}
      props={{
        ...props,
        dataFormatter: (data: any) => data.registry_errors,
        enableDownload: false,
        enableFilters: false,
        enableSearch: false,
        params: {
          ...props.params
        }
      }}
    />
  );
}
