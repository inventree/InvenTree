import type FullCalendar from '@fullcalendar/react';
import type { DateValue } from '@mantine/dates';
import { useLocalStorage } from '@mantine/hooks';
import { useCallback, useRef, useState } from 'react';
import type { TableFilter } from '../tables/Filter';

/*
 * Type definition for representing the state of a calendar:
 *
 * ref: A reference to the FullCalendar component
 * activeFilters: An array of active filters (saved to local storage)
 * setActiveFilters: A function to set the active filters
 * clearActiveFilters: A function to clear all active filters
 * monthName: The name of the current month (e.g. "January 2022")
 * setMonthName: A function to set the month name
 * searchTerm: The current search term for the calendar
 * setSearchTerm: A function to set the search term
 * nextMonth: A function to navigate to the next month
 * prevMonth: A function to navigate to the previous month
 * currentMonth: A function to navigate to the current month
 * selectMonth: A function to select a specific month
 */
export type CalendarState = {
  ref: React.RefObject<FullCalendar>;
  activeFilters: TableFilter[];
  setActiveFilters: (filters: TableFilter[]) => void;
  clearActiveFilters: () => void;
  monthName: string;
  setMonthName: (name: string) => void;
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  nextMonth: () => void;
  prevMonth: () => void;
  currentMonth: () => void;
  selectMonth: (date: DateValue) => void;
};

export default function useCalendar(calendarName: string): CalendarState {
  const ref = useRef<FullCalendar | null>(null);

  const [searchTerm, setSearchTerm] = useState<string>('');

  const [monthName, setMonthName] = useState<string>('');

  // Array of active filters (saved to local storage)
  const [activeFilters, setActiveFilters] = useLocalStorage<TableFilter[]>({
    key: `inventree-table-filters-${calendarName}`,
    defaultValue: [],
    getInitialValueInEffect: false
  });

  // Callback to clear all active filters from the table
  const clearActiveFilters = useCallback(() => {
    setActiveFilters([]);
  }, []);

  // Navigate to the previous month
  const prevMonth = useCallback(() => {
    ref.current?.getApi().prev();
  }, [ref]);

  // Navigate to the next month
  const nextMonth = useCallback(() => {
    ref.current?.getApi().next();
  }, [ref]);

  // Navigate to the current month
  const currentMonth = useCallback(() => {
    ref.current?.getApi().today();
  }, [ref]);

  // Callback to select a specific month from a picker
  const selectMonth = useCallback(
    (date: DateValue) => {
      if (date && ref?.current) {
        const api = ref.current.getApi();

        api.gotoDate(date);
      }
    },
    [ref]
  );

  return {
    activeFilters,
    setActiveFilters,
    clearActiveFilters,
    ref,
    monthName,
    setMonthName,
    searchTerm,
    setSearchTerm,
    nextMonth,
    prevMonth,
    currentMonth,
    selectMonth
  };
}
