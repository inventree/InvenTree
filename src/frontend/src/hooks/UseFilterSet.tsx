import type { FilterSetState, TableFilter } from '@lib/types/Filters';
import { useLocalStorage } from '@mantine/hooks';
import { useCallback } from 'react';

export function useFilterSet(filterKey: string): FilterSetState {
  // Array of active filters (saved to local storage)
  const [activeFilters, setActiveFilters] = useLocalStorage<TableFilter[]>({
    key: `inventree-filterset-${filterKey}`,
    defaultValue: [],
    sync: false,
    getInitialValueInEffect: false
  });

  // Callback to clear all active filters from the table
  const clearActiveFilters = useCallback(() => {
    setActiveFilters([]);
  }, []);

  return {
    filterKey,
    activeFilters,
    setActiveFilters,
    clearActiveFilters
  };
}
