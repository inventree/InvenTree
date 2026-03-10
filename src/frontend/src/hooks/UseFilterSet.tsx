import type { FilterSetState, TableFilter } from '@lib/types/Filters';
import { useLocalStorage } from '@mantine/hooks';
import { useCallback, useMemo } from 'react';

export function useFilterSet(
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

  const activeFilters: TableFilter[] = useMemo(() => {
    if (storedFilters == null) {
      // If there are no stored filters, set initial values
      const filters = initialFilters || [];
      setStoredFilters(filters);
      return filters;
    }
    return storedFilters || [];
  }, [storedFilters]);

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
