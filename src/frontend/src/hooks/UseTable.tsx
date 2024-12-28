import { randomId, useLocalStorage } from '@mantine/hooks';
import { useCallback, useMemo, useState } from 'react';
import { type SetURLSearchParams, useSearchParams } from 'react-router-dom';

import type { TableFilter } from '../tables/Filter';

/*
 * Type definition for representing the state of a table:
 *
 * tableKey: A unique key for the table. When this key changes, the table will be refreshed.
 * refreshTable: A callback function to externally refresh the table.
 * isLoading: A boolean flag to indicate if the table is currently loading data
 * setIsLoading: A function to set the isLoading flag
 * activeFilters: An array of active filters (saved to local storage)
 * setActiveFilters: A function to set the active filters
 * clearActiveFilters: A function to clear all active filters
 * queryFilters: A map of query filters (e.g. ?active=true&overdue=false) passed in the URL
 * setQueryFilters: A function to set the query filters
 * clearQueryFilters: A function to clear all query filters
 * expandedRecords: An array of expanded records (rows) in the table
 * setExpandedRecords: A function to set the expanded records
 * isRowExpanded: A function to determine if a record is expanded
 * selectedRecords: An array of selected records (rows) in the table
 * selectedIds: An array of primary key values for selected records
 * hasSelectedRecords: A boolean flag to indicate if any records are selected
 * setSelectedRecords: A function to set the selected records
 * clearSelectedRecords: A function to clear all selected records
 * hiddenColumns: An array of hidden column names
 * setHiddenColumns: A function to set the hidden columns
 * searchTerm: The current search term for the table
 * setSearchTerm: A function to set the search term
 * recordCount: The total number of records in the table
 * setRecordCount: A function to set the record count
 * page: The current page number
 * setPage: A function to set the current page number
 * pageSize: The number of records per page
 * setPageSize: A function to set the number of records per page
 * records: An array of records (rows) in the table
 * setRecords: A function to set the records
 * updateRecord: A function to update a single record in the table
 * idAccessor: The name of the primary key field in the records (default = 'pk')
 */
export type TableState = {
  tableKey: string;
  refreshTable: () => void;
  isLoading: boolean;
  setIsLoading: (value: boolean) => void;
  activeFilters: TableFilter[];
  setActiveFilters: (filters: TableFilter[]) => void;
  clearActiveFilters: () => void;
  queryFilters: URLSearchParams;
  setQueryFilters: SetURLSearchParams;
  clearQueryFilters: () => void;
  expandedRecords: any[];
  setExpandedRecords: (records: any[]) => void;
  isRowExpanded: (pk: number) => boolean;
  selectedRecords: any[];
  selectedIds: any[];
  hasSelectedRecords: boolean;
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
  pageSize: number;
  setPageSize: (pageSize: number) => void;
  records: any[];
  setRecords: (records: any[]) => void;
  updateRecord: (record: any) => void;
  idAccessor?: string;
};

/**
 * A custom hook for managing the state of an <InvenTreeTable> component.
 *
 * Refer to the TableState type definition for more information.
 */

export function useTable(tableName: string, idAccessor = 'pk'): TableState {
  // Function to generate a new ID (to refresh the table)
  function generateTableName() {
    return `${tableName.replaceAll('-', '')}-${randomId()}`;
  }

  // Extract URL query parameters (e.g. ?active=true&overdue=false)
  const [queryFilters, setQueryFilters] = useSearchParams();

  const clearQueryFilters = useCallback(() => {
    setQueryFilters({});
  }, []);

  const [tableKey, setTableKey] = useState<string>(generateTableName());

  // Callback used to refresh (reload) the table
  const refreshTable = useCallback(() => {
    setTableKey(generateTableName());
  }, [generateTableName]);

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

  // Function to determine if a record is expanded
  const isRowExpanded = useCallback(
    (pk: number) => {
      return expandedRecords.includes(pk);
    },
    [expandedRecords]
  );

  // Array of selected records
  const [selectedRecords, setSelectedRecords] = useState<any[]>([]);

  // Array of selected primary key values
  const selectedIds = useMemo(
    () => selectedRecords.map((r) => r[idAccessor || 'pk']),
    [selectedRecords]
  );

  const clearSelectedRecords = useCallback(() => {
    setSelectedRecords([]);
  }, []);

  const hasSelectedRecords = useMemo(() => {
    return selectedRecords.length > 0;
  }, [selectedRecords]);

  // Total record count
  const [recordCount, setRecordCount] = useState<number>(0);

  // Pagination data
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(25);

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
      const _records = [...records];

      // Find the matching record in the table
      const index = _records.findIndex(
        (r) => r[idAccessor || 'pk'] === record.pk
      );

      if (index >= 0) {
        _records[index] = {
          ..._records[index],
          ...record
        };
      } else {
        _records.push(record);
      }

      setRecords(_records);
    },
    [records]
  );

  const [isLoading, setIsLoading] = useState<boolean>(false);

  return {
    tableKey,
    refreshTable,
    isLoading,
    setIsLoading,
    activeFilters,
    setActiveFilters,
    clearActiveFilters,
    queryFilters,
    setQueryFilters,
    clearQueryFilters,
    expandedRecords,
    setExpandedRecords,
    isRowExpanded,
    selectedRecords,
    selectedIds,
    setSelectedRecords,
    clearSelectedRecords,
    hasSelectedRecords,
    hiddenColumns,
    setHiddenColumns,
    searchTerm,
    setSearchTerm,
    recordCount,
    setRecordCount,
    page,
    setPage,
    pageSize,
    setPageSize,
    records,
    setRecords,
    updateRecord,
    idAccessor
  };
}
