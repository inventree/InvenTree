import { randomId } from '@mantine/hooks';
import { useCallback, useState } from 'react';

/**
 * Custom hook for refreshing an InvenTreeTable externally
 * Returns a unique ID for the table, which can be updated to trigger a refresh of the <table className=""></table>
 *
 * @returns { tableKey, refreshTable }
 *
 * To use this hook:
 * const { tableKey, refreshTable } = useTableRefresh();
 *
 * Then, pass the refreshId to the InvenTreeTable component:
 * <InvenTreeTable tableKey={tableKey} ... />
 */
export function useTableRefresh(tableName: string) {
  const [tableKey, setTableKey] = useState<string>(generateTableName());

  function generateTableName() {
    return `${tableName}-${randomId()}`;
  }

  // Generate a new ID to refresh the table
  const refreshTable = useCallback(function () {
    setTableKey(generateTableName());
  }, []);

  return { tableKey, refreshTable };
}
