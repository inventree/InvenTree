import { randomId } from '@mantine/hooks';
import { useCallback, useState } from 'react';

export type TableState = {
  tableKey: string;
  refreshTable: () => void;
};

/**
 * A custom hook for managing the state of an <InvenTreeTable> component.
 *
 * tableKey: A unique key for the table. When this key changes, the table will be refreshed.
 * refreshTable: A callback function to externally refresh the table.
 *
 */

export function useTable(tableName: string): TableState {
  // Function to generate a new ID (to refresh the table)
  function generateTableName() {
    return `${tableName}-${randomId()}`;
  }

  const [tableKey, setTableKey] = useState<string>(generateTableName());

  // Callback used to refresh (reload) the table
  const refreshTable = useCallback(() => {
    setTableKey(generateTableName());
  }, []);

  return {
    tableKey,
    refreshTable
  };
}
