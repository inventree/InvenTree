import { randomId, useLocalStorage } from '@mantine/hooks';
import { useCallback, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import type { FilterSetState } from '@lib/types/Filters';
import type { TableState } from '@lib/types/Tables';
import { useFilterSet } from './UseFilterSet';

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

  const filterSet: FilterSetState = useFilterSet(`table-${tableName}`);

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

  const [pageSizeLoaded, setPageSizeLoaded] = useState<boolean>(false);

  // Pagination data
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useLocalStorage<number>({
    key: 'inventree-table-page-size',
    defaultValue: 25,
    sync: false,
    deserialize: (value: string | undefined) => {
      setPageSizeLoaded(true);
      return value === undefined ? 25 : JSON.parse(value);
    }
  });

  const [hiddenColumnsLoaded, setHiddenColumnsLoaded] =
    useState<boolean>(false);

  // A list of hidden columns, saved to local storage
  const [hiddenColumns, setHiddenColumns] = useLocalStorage<string[] | null>({
    key: `inventree-hidden-table-columns-${tableName}`,
    defaultValue: null,
    sync: false,
    deserialize: (value) => {
      setHiddenColumnsLoaded(true);
      return value === undefined ? null : JSON.parse(value);
    }
  });

  const storedDataLoaded = useMemo(() => {
    return pageSizeLoaded && hiddenColumnsLoaded;
  }, [pageSizeLoaded, hiddenColumnsLoaded]);

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
    filterSet,
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
    storedDataLoaded,
    records,
    setRecords,
    updateRecord,
    idAccessor
  };
}
