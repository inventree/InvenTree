import { useLocalStorage } from '@mantine/hooks';
import { useCallback, useEffect, useMemo } from 'react';
import type {
  FilterSetState,
  NamedFilterSet,
  TableFilter
} from '../types/Filters';

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

  // Named filter set snapshots (saved to local storage, separate key)
  const [storedNamedSets, setStoredNamedSets] = useLocalStorage<
    NamedFilterSet[]
  >({
    key: `inventree-filtersets-${filterKey}`,
    defaultValue: [],
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

  const clearActiveFilters = useCallback(() => {
    setStoredFilters([]);
  }, []);

  const setActiveFilters = useCallback(
    (filters: TableFilter[]) => {
      setStoredFilters(filters);
    },
    [setStoredFilters]
  );

  const saveFilterSet = useCallback(
    (name: string) => {
      const snapshot = activeFilters.map(
        ({ name: n, value, displayValue }) => ({
          name: n,
          value,
          displayValue
        })
      );
      setStoredNamedSets((prev) => {
        const without = (prev ?? []).filter((s) => s.name !== name);
        return [...without, { name, filters: snapshot }];
      });
    },
    [activeFilters, setStoredNamedSets]
  );

  const loadFilterSet = useCallback(
    (name: string) => {
      const saved = (storedNamedSets ?? []).find((s) => s.name === name);
      if (saved) {
        setStoredFilters(saved.filters as TableFilter[]);
      }
    },
    [storedNamedSets, setStoredFilters]
  );

  const deleteFilterSet = useCallback(
    (name: string) => {
      setStoredNamedSets((prev) => (prev ?? []).filter((s) => s.name !== name));
    },
    [setStoredNamedSets]
  );

  return {
    filterKey,
    activeFilters,
    setActiveFilters,
    clearActiveFilters,
    savedFilterSets: storedNamedSets ?? [],
    saveFilterSet,
    loadFilterSet,
    deleteFilterSet
  };
}
