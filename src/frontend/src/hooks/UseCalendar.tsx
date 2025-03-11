import type FullCalendar from '@fullcalendar/react';
import type { DateValue } from '@mantine/dates';
import { useLocalStorage } from '@mantine/hooks';
import { type UseQueryResult, useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { useCallback, useMemo, useRef, useState } from 'react';
import { api } from '../App';
import type { ApiEndpoints } from '../enums/ApiEndpoints';
import { showApiErrorMessage } from '../functions/notifications';
import { apiUrl } from '../states/ApiState';
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
 * startDate: The start date of the current date range
 * setStartDate: A function to set the start date
 * endDate: The end date of the current date range
 * setEndDate: A function to set the end date
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
  startDate: Date | null;
  setStartDate: (date: Date | null) => void;
  endDate: Date | null;
  setEndDate: (date: Date | null) => void;
  setSearchTerm: (term: string) => void;
  nextMonth: () => void;
  prevMonth: () => void;
  currentMonth: () => void;
  selectMonth: (date: DateValue) => void;
  query: UseQueryResult;
  data: any;
};

export default function useCalendar({
  name,
  endpoint,
  queryParams
}: {
  name: string;
  endpoint: ApiEndpoints;
  queryParams?: any;
}): CalendarState {
  const ref = useRef<FullCalendar | null>(null);

  const [searchTerm, setSearchTerm] = useState<string>('');

  const [monthName, setMonthName] = useState<string>('');

  const [startDate, setStartDate] = useState<Date | null>(null);

  const [endDate, setEndDate] = useState<Date | null>(null);

  // Array of active filters (saved to local storage)
  const [activeFilters, setActiveFilters] = useLocalStorage<TableFilter[]>({
    key: `inventree-calendar-filters-${name}`,
    defaultValue: [],
    getInitialValueInEffect: false
  });

  // Callback to clear all active filters from the table
  const clearActiveFilters = useCallback(() => {
    setActiveFilters([]);
  }, []);

  // Generate a set of API query filters
  const queryFilters = useMemo(() => {
    // Expand date range by one month, to ensure we capture all events

    return {
      min_date: startDate
        ? dayjs(startDate).subtract(1, 'month').toISOString().split('T')[0]
        : null,
      max_date: endDate
        ? dayjs(endDate).add(1, 'month').toISOString().split('T')[0]
        : null,
      search: searchTerm,
      ...(queryParams || {})
    };
  }, [startDate, endDate, searchTerm, activeFilters, queryParams]);

  const query = useQuery({
    enabled: !!startDate && !!endDate,
    queryKey: ['calendar', name, endpoint, queryFilters],
    queryFn: async () => {
      // Fetch data from the API
      return api
        .get(apiUrl(endpoint), {
          params: queryFilters
        })
        .then((response) => {
          return response.data ?? [];
        })
        .catch((error) => {
          showApiErrorMessage({
            error: error,
            title: 'Error fetching calendar data'
          });
        });
    }
  });

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
    selectMonth,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    query: query,
    data: query.data
  };
}
