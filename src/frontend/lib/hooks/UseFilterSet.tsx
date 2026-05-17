import { useLocalStorage } from '@mantine/hooks';
import { useCallback, useEffect, useMemo } from 'react';
import type { FilterSetState, TableFilter } from '../types/Filters';

export default function useFilterSet(
  filterKey: string,
  initialFilters?: TableFilter[]
): FilterSetState {
  // Array of active filters (saved to local storage)
  const [storedFilters, setStoredFilters] = useLocalStorage<
    TableFilter[] | null
  >({
    key: `inventree-filterset-${filterKey}`,
    defaultValue: null,
    sync: false,
    getInitialValueInEffect: false
  });

  useEffect(() => {
    if (storedFilters == null) {
      setStoredFilters(initialFilters || []);
    }
  }, [storedFilters, initialFilters, setStoredFilters]);

  const activeFilters: TableFilter[] = useMemo(() => {
    return storedFilters ?? initialFilters ?? [];
  }, [storedFilters, initialFilters]);

  // Callback to clear all active filters from the table
  const clearActiveFilters = useCallback(() => {
    setStoredFilters([]);
  }, []);

  const setActiveFilters = useCallback(
    (filters: TableFilter[]) => {
      setStoredFilters(filters);
    },
    [setStoredFilters]
  );

  return {
    filterKey,
    activeFilters,
    setActiveFilters,
    clearActiveFilters
  };
}
