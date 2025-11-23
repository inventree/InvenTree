import { ApiEndpoints, type ModelType, apiUrl } from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { useCallback, useMemo } from 'react';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Construct a table listing parameters
 */
export function ParameterTable({
  modelType,
  modelId
}: {
  modelType: ModelType;
  modelId: number;
}) {
  const table = useTable('parameters');
  const user = useUserState();

  const tableColumns: TableColumn[] = useMemo(() => {
    // TODO
    return [];
  }, [user]);

  const tableFilters: TableFilter[] = useMemo(() => {
    // TODO
    return [];
  }, []);

  const tableActions = useMemo(() => {
    // TODO
    return [];
  }, [user]);

  const rowActions = useCallback(() => {
    return [];
  }, [user]);

  return (
    <>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.parameter_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableDownload: true,
          rowActions: rowActions,
          tableActions: tableActions,
          tableFilters: tableFilters,
          params: {
            model_type: modelType,
            model_id: modelId
          }
        }}
      />
    </>
  );
}
