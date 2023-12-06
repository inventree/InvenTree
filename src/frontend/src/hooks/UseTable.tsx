import { randomId, useLocalStorage } from '@mantine/hooks';
import { useCallback, useState } from 'react';

import { TableFilter } from '../components/tables/Filter';

/*
 * Type definition for representing the state of a table:
 *
 * tableKey: A unique key for the table. When this key changes, the table will be refreshed.
 * refreshTable: A callback function to externally refresh the table.
 * activeFilters: An array of active filters (saved to local storage)
 */
export type TableState = {
  tableKey: string;
  activeFilters: TableFilter[];
  setActiveFilters: (filters: TableFilter[]) => void;
  clearActiveFilters: () => void;
  refreshTable: () => void;
};

/**
 * A custom hook for managing the state of an <InvenTreeTable> component.
 *
 * Refer to the TableState type definition for more information.
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

  // Array of active filters (saved to local storage)
  const [activeFilters, setActiveFilters] = useLocalStorage<TableFilter[]>({
    key: `inventree-table-filters-${tableName}`,
    defaultValue: [],
    getInitialValueInEffect: false
  });

  // Callback to clear all active filters from the table
  const clearActiveFilters = useCallback(() => {
    setActiveFilters([]);
  }, []);

  return {
    tableKey,
    activeFilters,
    setActiveFilters,
    clearActiveFilters,
    refreshTable
  };
}
