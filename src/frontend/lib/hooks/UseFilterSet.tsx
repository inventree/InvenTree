import { useLocalStorage } from '@mantine/hooks';
import { useCallback } from 'react';

import type { TableFilter } from '../tables/Filter';

/*
 * Type definition for representing the state of a group of filters.
 * These may be applied to a data view (e.g. table, calendar) to filter the displayed data.
 *
 * filterKey: A unique key for the filter set
 * activeFilters: An array of active filters
 * setActiveFilters: A function to set the active filters
 * clearActiveFilters: A function to clear all active filters
 */
export type FilterSetState = {
  filterKey: string;
  activeFilters: TableFilter[];
  setActiveFilters: (filters: TableFilter[]) => void;
  clearActiveFilters: () => void;
};

export function useFilterSet(filterKey: string): FilterSetState {
  // Array of active filters (saved to local storage)
  const [activeFilters, setActiveFilters] = useLocalStorage<TableFilter[]>({
    key: `inventree-filterset-${filterKey}`,
    defaultValue: [],
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
