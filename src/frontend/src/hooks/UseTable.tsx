import { randomId, useLocalStorage } from '@mantine/hooks';
import { useCallback, useState } from 'react';

import { TableFilter } from '../tables/Filter';

/*
 * Type definition for representing the state of a table:
 *
 * tableKey: A unique key for the table. When this key changes, the table will be refreshed.
 * refreshTable: A callback function to externally refresh the table.
 * activeFilters: An array of active filters (saved to local storage)
 * selectedRecords: An array of selected records (rows) in the table
 * hiddenColumns: An array of hidden column names
 * searchTerm: The current search term for the table
 */
export type TableState = {
  tableKey: string;
  refreshTable: () => void;
  activeFilters: TableFilter[];
  setActiveFilters: (filters: TableFilter[]) => void;
  clearActiveFilters: () => void;
  expandedRecords: any[];
  setExpandedRecords: (records: any[]) => void;
  selectedRecords: any[];
  setSelectedRecords: (records: any[]) => void;
  clearSelectedRecords: () => void;
  hiddenColumns: string[];
  setHiddenColumns: (columns: string[]) => void;
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  recordCount: number;
  setRecordCount: (count: number) => void;
  page: number;
  setPage: (page: number) => void;
  records: any[];
  setRecords: (records: any[]) => void;
  updateRecord: (record: any) => void;
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

  // Array of expanded records
  const [expandedRecords, setExpandedRecords] = useState<any[]>([]);

  // Array of selected records
  const [selectedRecords, setSelectedRecords] = useState<any[]>([]);

  const clearSelectedRecords = useCallback(() => {
    setSelectedRecords([]);
  }, []);

  // Total record count
  const [recordCount, setRecordCount] = useState<number>(0);

  // Pagination data
  const [page, setPage] = useState<number>(1);

  // A list of hidden columns, saved to local storage
  const [hiddenColumns, setHiddenColumns] = useLocalStorage<string[]>({
    key: `inventree-hidden-table-columns-${tableName}`,
    defaultValue: []
  });

  // Search term
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Table records
  const [records, setRecords] = useState<any[]>([]);

  // Update a single record in the table, by primary key value
  const updateRecord = useCallback(
    (record: any) => {
      let _records = [...records];

      // Find the matching record in the table
      const index = _records.findIndex((r) => r.pk === record.pk);

      if (index >= 0) {
        _records[index] = record;
      } else {
        _records.push(record);
      }

      setRecords(_records);
    },
    [records]
  );

  return {
    tableKey,
    refreshTable,
    activeFilters,
    setActiveFilters,
    clearActiveFilters,
    expandedRecords,
    setExpandedRecords,
    selectedRecords,
    setSelectedRecords,
    clearSelectedRecords,
    hiddenColumns,
    setHiddenColumns,
    searchTerm,
    setSearchTerm,
    recordCount,
    setRecordCount,
    page,
    setPage,
    records,
    setRecords,
    updateRecord
  };
}
