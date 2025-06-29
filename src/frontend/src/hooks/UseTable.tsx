import { randomId, useLocalStorage } from '@mantine/hooks';
import { useCallback, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import type { FilterSetState } from '@lib/types/Filters';
import type { TableState } from '@lib/types/Tables';
import { useFilterSet } from './UseFilterSet';

// Interface for the stored table data in local storage
interface StoredTableData {
  hiddenColumns: string[] | null;
}

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

  const [page, setPage] = useState<number>(1);

  const [storedDataLoaded, setStoredDataLoaded] = useState<boolean>(false);

  const [tableData, setTableData] = useState<StoredTableData>({
    hiddenColumns: null
  });

  const [storedTableData, setStoredTableData] =
    useLocalStorage<StoredTableData>({
      key: `inventree-table-data-${tableName}`,
      getInitialValueInEffect: true,
      // sync: false,  // Do not use this option - see below
      defaultValue: {
        hiddenColumns: null
      },
      deserialize: (value: any) => {
        const tableData =
          value === undefined
            ? {
                hiddenColumns: null
              }
            : JSON.parse(value);

        if (!storedDataLoaded) {
          setStoredDataLoaded((wasLoaded: boolean) => {
            if (!wasLoaded) {
              // First load of stored table data - copy to local state
              // We only do this on first load, to avoid live syncing between tabs
              // Note: The 'sync: false' option is not used, it does not perform as expected
              setTableData(tableData);
            }
            return true;
          });
        }
        return tableData;
      }
    });

  const setHiddenColumns = useCallback((columns: string[] | null) => {
    setStoredTableData((prev) => {
      return {
        ...prev,
        hiddenColumns: columns
      };
    });
    setTableData((prev) => ({
      ...prev,
      hiddenColumns: columns
    }));
  }, []);

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
    hiddenColumns: tableData.hiddenColumns,
    setHiddenColumns,
    searchTerm,
    setSearchTerm,
    recordCount,
    setRecordCount,
    page,
    setPage,
    storedDataLoaded,
    records,
    setRecords,
    updateRecord,
    idAccessor
  };
}
